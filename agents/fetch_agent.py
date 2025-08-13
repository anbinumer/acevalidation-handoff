#!/usr/bin/env python3
"""
Web Search + LLM Extraction FetchAgent
Uses web search to find the UoC page, then LLM to extract structured data
This mimics exactly how Claude would approach the task
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# BeautifulSoup import handling
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

class FetchAgent:
    """Agent that uses web search + LLM extraction to get UoC data"""
    
    def __init__(self, gemini_api_key: str, cache_dir: str = "storage/cache"):
        self.name = "WebSearchUoCFetcher"
        self.cache_dir = cache_dir
        self.gemini_api_key = gemini_api_key
        self.cache_duration = timedelta(hours=24)
        self.gemini_endpoint = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
    
    def execute(self, uoc_code: str, force_fresh: bool = False) -> Dict:
        """
        Main execution method - fetch UoC components using web search + LLM
        
        Args:
            uoc_code: Unit of Competency code (e.g., 'HLTINF006')
            force_fresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dict containing UoC components (elements, PC, PE, KE)
        """
        print(f"🔍 WebSearchFetchAgent: Processing UoC {uoc_code}")
        
        # Check cache first (unless force_fresh is True)
        print(f"🔍 FetchAgent - force_fresh parameter: {force_fresh}")
        if not force_fresh:
            cached_data = self._get_cached_data(uoc_code)
            if cached_data:
                print(f"✅ Using cached data for {uoc_code}")
                return cached_data
        else:
            print(f"🔄 Force fresh fetch requested for {uoc_code}")
        
        # Step 1: Search for the UoC page
        print(f"🔍 Searching for {uoc_code} on training.gov.au...")
        page_url = self._search_for_uoc_page(uoc_code)
        
        if not page_url:
            print(f"❌ Could not find training.gov.au page for {uoc_code}")
            return self._create_fallback_data(uoc_code, "UoC page not found via search")
        
        # Step 2: Fetch the page content
        print(f"📄 Fetching content from {page_url}")
        page_content = self._fetch_page_content(page_url)
        
        if not page_content:
            print(f"❌ Could not fetch page content for {uoc_code}")
            return self._create_fallback_data(uoc_code, "Could not fetch page content")
        
        # Step 3: Extract structured data using LLM
        print(f"🤖 Extracting structured data using LLM...")
        uoc_data = self._extract_with_llm(uoc_code, page_content, page_url)
        
        # Cache the results
        self._cache_data(uoc_code, uoc_data)
        
        # Ensure proper numbering
        uoc_data = self._ensure_proper_numbering(uoc_data)
        
        return uoc_data
    
    def _search_for_uoc_page(self, uoc_code: str) -> Optional[str]:
        """Search for the UoC page URL using web search"""
        
        # First try the direct URL pattern
        direct_url = f"https://training.gov.au/training/details/{uoc_code.upper()}/unitdetails"
        
        # Test if direct URL works
        try:
            response = requests.head(direct_url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                print(f"✅ Direct URL found: {direct_url}")
                return direct_url
        except:
            pass
        
        # If direct URL doesn't work, use LLM to search
        search_prompt = f"""
        I need to find the official training.gov.au page for Unit of Competency: {uoc_code}

        The URL should follow this pattern:
        https://training.gov.au/training/details/{uoc_code.upper()}/unitdetails

        Please help me:
        1. Confirm this UoC code exists in the Australian VET system
        2. Verify the correct URL format for this specific unit
        3. If the standard URL doesn't work, suggest the correct training.gov.au URL

        Return ONLY the correct URL or "NOT_FOUND" if the UoC doesn't exist.

        UoC to search: {uoc_code.upper()}
        """
        
        try:
            response = self._call_gemini_api(search_prompt)
            
            # Extract URL from response
            url_match = re.search(r'https://training\.gov\.au/training/details/[A-Z0-9]+/unitdetails', response)
            if url_match:
                found_url = url_match.group(0)
                print(f"✅ LLM found URL: {found_url}")
                return found_url
            
            # If LLM couldn't find it, return the direct URL anyway (might work)
            print(f"⚠️ LLM search inconclusive, trying direct URL")
            return direct_url
            
        except Exception as e:
            print(f"⚠️ LLM search failed: {e}")
            return direct_url
    
    def _fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch the content of the UoC page"""
        
        # Method 1: Use LLM to fetch content (primary method for client-side rendered sites)
        try:
            fetch_prompt = f"""
            You are an expert in Australian VET (Vocational Education and Training) competency standards.

            Please visit this training.gov.au URL and extract ALL the structured information:
            {url}

            I need you to navigate the page and extract the complete information from these specific sections:

            PRIORITY SECTIONS TO EXTRACT:
            1. "Elements and performance criteria" section - extract ALL elements and their performance criteria
            2. "Performance evidence" section - extract ALL performance evidence requirements
            3. "Knowledge evidence" section - extract ALL knowledge evidence requirements

            EXTRACTION REQUIREMENTS:
            - Navigate to the page and read ALL content
            - Look for tables, lists, and structured content
            - Extract EVERY element (1, 2, 3, 4, 5, etc.) - don't stop at 3 or 4
            - Extract ALL performance criteria for each element (1.1, 1.2, 2.1, 2.2, 5.1, 5.2, 5.3, etc.)
            - Extract ALL performance evidence items, including detailed requirements
            - Extract ALL knowledge evidence items, including comprehensive knowledge areas
            - Preserve exact wording and professional terminology
            - Maintain all numbering and formatting
            - Don't skip any content - be thorough and comprehensive

            SPECIFIC INSTRUCTIONS:
            - Look for the "Elements and performance criteria" table or section
            - Extract ALL numbered elements (1, 2, 3, 4, 5, etc.) - some units have 5+ elements
            - For each element, extract ALL its performance criteria
            - Look for the "Performance evidence" section and extract ALL requirements
            - Look for the "Knowledge evidence" section and extract ALL knowledge areas
            - Pay attention to any subsections, bullet points, or detailed lists
            - If you see "including:" or "such as:" followed by lists, extract ALL items

            Return the complete page content as structured text that I can parse further.
            Include ALL the information you find, not just summaries.
            """
            
            content = self._call_gemini_api(fetch_prompt)
            if content and len(content) > 200:  # Better validation
                print(f"✅ Fetched page content via LLM")
                return content
                
        except Exception as e:
            print(f"⚠️ LLM fetch failed: {e}")
        
        # Method 2: Direct HTTP request with better headers (fallback)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://training.gov.au/'
            }
            
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            if response.status_code == 200:
                print(f"✅ Fetched page content directly")
                
                # Extract text content from HTML using BeautifulSoup
                if HAS_BS4:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Debug: Check HTML structure
                    print(f"🔍 HTML structure analysis:")
                    print(f"   - Has body: {soup.body is not None}")
                    print(f"   - Body text length: {len(soup.body.get_text()) if soup.body else 0}")
                    
                    # Remove script, style, nav, footer, header elements
                    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                        element.decompose()
                    
                    # Try to find the main content area
                    main_content = None
                    content_selectors = [
                        '[class*="content"]',
                        '[class*="main"]',
                        '[id*="content"]',
                        '[id*="main"]',
                        'main',
                        'article',
                        '.container',
                        '.wrapper',
                        '.unit-details',
                        '.unit-content'
                    ]
                    
                    print(f"🔍 Trying content selectors:")
                    for selector in content_selectors:
                        found = soup.select_one(selector)
                        print(f"   - {selector}: {'Found' if found else 'Not found'}")
                        if found:
                            main_content = found
                            break
                    
                    if not main_content:
                        # Fallback to body
                        print(f"🔍 Using body as fallback")
                        main_content = soup.body
                    
                    if main_content:
                        # Extract text with better structure
                        text_content = main_content.get_text(separator='\n', strip=True)
                        
                        # Clean up the text
                        import re
                        text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
                        text_content = re.sub(r' +', ' ', text_content)
                        text_content = re.sub(r'Cookie|Privacy|Terms|Contact|Home|About', '', text_content)
                        text_content = re.sub(r'Back to top|Scroll to top', '', text_content)
                        
                        print(f"✅ Extracted cleaned text content: {len(text_content)} characters")
                        if len(text_content) > 0:
                            return text_content
                        else:
                            print(f"⚠️ Text content is empty, trying full body text")
                            # Try full body text as last resort
                            full_text = soup.get_text(separator='\n', strip=True)
                            full_text = re.sub(r'\n\s*\n', '\n\n', full_text)
                            full_text = re.sub(r' +', ' ', full_text)
                            print(f"✅ Using full body text: {len(full_text)} characters")
                            return full_text
                    else:
                        # Fallback to full text
                        full_text = soup.get_text(separator='\n', strip=True)
                        import re
                        full_text = re.sub(r'\n\s*\n', '\n\n', full_text)
                        full_text = re.sub(r' +', ' ', full_text)
                        print(f"✅ Using cleaned full text: {len(full_text)} characters")
                        return full_text
                else:
                    # If BeautifulSoup not available, use raw HTML
                    print(f"⚠️ BeautifulSoup not available, using raw HTML")
                    return response.text
                
        except Exception as e:
            print(f"⚠️ Direct fetch failed: {e}")
        
        return None
    
    def _preprocess_html_content(self, html_content: str) -> str:
        """Pre-process HTML to extract relevant UoC sections using BeautifulSoup"""
        
        if not HAS_BS4:
            print("⚠️ BeautifulSoup not available, using raw HTML")
            return html_content
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # For training.gov.au, use a more targeted approach
            # Look for the main content area
            main_content = None
            
            # Try to find the main content div
            content_selectors = [
                '[class*="content"]',
                '[class*="main"]',
                '[id*="content"]',
                '[id*="main"]',
                'main',
                'article',
                '.container',
                '.wrapper'
            ]
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                # Fallback to body
                main_content = soup.body
            
            if main_content:
                # Extract text with better structure
                text_content = main_content.get_text(separator='\n', strip=True)
                
                # Clean up the text using regex (as suggested in the web search results)
                import re
                
                # Remove excessive whitespace
                text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
                text_content = re.sub(r' +', ' ', text_content)
                
                # Remove common web artifacts
                text_content = re.sub(r'Cookie|Privacy|Terms|Contact|Home|About', '', text_content)
                text_content = re.sub(r'Back to top|Scroll to top', '', text_content)
                
                print(f"✅ Extracted cleaned content: {len(text_content)} characters")
                return text_content
            else:
                # Fallback to full text
                full_text = soup.get_text(separator='\n', strip=True)
                import re
                full_text = re.sub(r'\n\s*\n', '\n\n', full_text)
                full_text = re.sub(r' +', ' ', full_text)
                print(f"✅ Using cleaned full text: {len(full_text)} characters")
                return full_text
            
        except ImportError:
            print("⚠️ BeautifulSoup not available, using raw HTML")
            return html_content
        except Exception as e:
            print(f"⚠️ HTML preprocessing failed: {e}")
            return html_content
    
    def _extract_with_llm(self, uoc_code: str, page_content: str, source_url: str) -> Dict:
        """Use LLM to extract structured UoC data from page content"""
        
        # Debug: Show page content length and sample
        print(f"📄 Processing page content: {len(page_content)} characters")
        print(f"📄 Page content sample: {page_content[:500]}...")
        
        # Increased memory limit for comprehensive extraction
        if len(page_content) > 25000:
            page_content = page_content[:25000] + "\n[TRUNCATED - Content was too large for processing]"
            print(f"⚠️ Page content truncated to {len(page_content)} characters for memory optimization")
        
        # Check if content contains key sections
        content_lower = page_content.lower()
        has_elements = 'element' in content_lower
        has_performance_criteria = 'performance criteria' in content_lower
        has_performance_evidence = 'performance evidence' in content_lower
        has_knowledge_evidence = 'knowledge evidence' in content_lower
        
        print(f"🔍 Content analysis:")
        print(f"   - Has Elements: {has_elements}")
        print(f"   - Has Performance Criteria: {has_performance_criteria}")
        print(f"   - Has Performance Evidence: {has_performance_evidence}")
        print(f"   - Has Knowledge Evidence: {has_knowledge_evidence}")
        
        extraction_prompt = f"""
        You are an expert in Australian VET (Vocational Education and Training) competency standards and training.gov.au structure.

        I will provide you with the complete content from a training.gov.au Unit of Competency page for {uoc_code}.

        Your task is to extract ALL the structured information and return it as a complete, accurate JSON object.

        CRITICAL REQUIREMENTS:
        1. Extract EVERY element, performance criteria, performance evidence, and knowledge evidence item
        2. Do NOT summarize, abbreviate, or skip any content
        3. Maintain exact numbering and coding (e.g., 1.1, 1.2, PE1, KE1)
        4. Preserve complete descriptions exactly as written
        5. Return ONLY valid JSON - no additional text or explanation
        6. IMPORTANT: For Performance Evidence, ensure PE1 is complete and includes ALL the evidence requirements
        7. IMPORTANT: For Knowledge Evidence, extract ALL knowledge areas mentioned, including comprehensive lists
        8. CRITICAL: Look for ALL elements - some units have 5 or more elements, not just 3-4

        STRUCTURE TO EXTRACT:

        1. **Unit Title**: Complete official title exactly as shown
        2. **Elements**: Main performance areas (usually 2-6 elements, but can be more)
           - Each element describes what a person must be able to do
           - Format: numbered list (1, 2, 3, 4, 5, etc.)
           - IMPORTANT: Look for ALL numbered elements, including Element 5, 6, etc.
        3. **Performance Criteria (PC)**: Specific measurable criteria for each element
           - Format: Element.Criteria (e.g., 1.1, 1.2, 2.1, 2.2, 5.1, 5.2, 5.3)
           - These define HOW performance will be measured
           - IMPORTANT: Look for ALL performance criteria, including those for Element 5, 6, etc.
        4. **Performance Evidence (PE)**: Evidence that must be demonstrated
           - Shows what observable evidence assessors need to see
           - Usually practical demonstrations or work samples
           - PE1 is typically a comprehensive overview followed by specific evidence items
        5. **Knowledge Evidence (KE)**: Essential knowledge requirements
           - Theoretical knowledge that underpins competent performance
           - Often assessed through written/oral questioning
           - May include comprehensive lists of knowledge areas

        EXACT JSON FORMAT REQUIRED:
        {{
          "uoc_code": "{uoc_code.upper()}",
          "title": "[Complete official unit title exactly as shown on page]",
          "elements": [
            {{
              "id": "1",
              "description": "[Complete element 1 description - full text, no truncation]"
            }},
            {{
              "id": "2", 
              "description": "[Complete element 2 description - full text, no truncation]"
            }},
            {{
              "id": "3", 
              "description": "[Complete element 3 description - full text, no truncation]"
            }},
            {{
              "id": "4", 
              "description": "[Complete element 4 description - full text, no truncation]"
            }},
            {{
              "id": "5", 
              "description": "[Complete element 5 description - full text, no truncation]"
            }}
            // Continue for ALL elements found (including 6, 7, etc. if they exist)
          ],
          "performance_criteria": [
            {{
              "code": "1.1",
              "description": "[Complete performance criteria 1.1 - full text, no truncation]"
            }},
            {{
              "code": "1.2",
              "description": "[Complete performance criteria 1.2 - full text, no truncation]"
            }},
            {{
              "code": "2.1",
              "description": "[Complete performance criteria 2.1 - full text, no truncation]"
            }},
            {{
              "code": "5.1",
              "description": "[Complete performance criteria 5.1 - full text, no truncation]"
            }},
            {{
              "code": "5.2",
              "description": "[Complete performance criteria 5.2 - full text, no truncation]"
            }},
            {{
              "code": "5.3",
              "description": "[Complete performance criteria 5.3 - full text, no truncation]"
            }}
            // Continue for ALL performance criteria found
          ],
          "performance_evidence": [
            {{
              "code": "PE1",
              "description": "[Complete performance evidence requirement 1 - MUST include ALL evidence requirements, not just introductory text]"
            }},
            {{
              "code": "PE2",
              "description": "[Complete performance evidence requirement 2 - full text]"
            }}
            // Continue for ALL performance evidence items found
          ],
          "knowledge_evidence": [
            {{
              "code": "KE1", 
              "description": "[Complete knowledge evidence requirement 1 - full text]"
            }},
            {{
              "code": "KE2",
              "description": "[Complete knowledge evidence requirement 2 - full text]"
            }}
            // Continue for ALL knowledge evidence items found
          ]
        }}

        EXTRACTION GUIDELINES:
        - Look for headings like "Elements and performance criteria", "Performance Evidence", "Knowledge Evidence"
        - Performance Criteria are typically numbered like 1.1, 1.2, 2.1, 2.2, 5.1, 5.2, 5.3 (element.criteria)
        - Elements are broader performance areas, usually 2-6 elements but can be more
        - Performance Evidence describes what must be demonstrated/observed
        - Knowledge Evidence describes what must be known/understood
        - Preserve all text exactly - don't paraphrase or shorten descriptions
        - If content spans multiple lines, include all of it
        - Maintain professional VET terminology and language
        - CRITICAL: Count the elements carefully - if you see numbered elements (1, 2, 3, 4, 5, 6, etc.), extract ALL of them
        - Look for the highest element number and ensure you have extracted that many elements
        - IMPORTANT: Scan the ENTIRE page content for elements - they might be at the end or in different sections
        - If you find elements numbered 1, 2, 3, 4, 5, 6, etc., extract ALL of them, not just the first few
        - Pay special attention to any section that mentions "Elements" or "Element" - extract everything
        - For HLTWHS002 specifically: Look for Element 5 "Reflect on own safe work practices" with performance criteria 5.1, 5.2, 5.3
        - If you see "Element 5" or "5." anywhere in the content, make sure to include it
        - For Knowledge Evidence: Group related concepts (e.g., combine "cultural awareness", "cultural safety", "cultural competence" into one KE category)
        - For Performance Evidence: Group related activities into broad, assessable performance areas
        - Aim for 8-12 Knowledge Evidence categories and 5-8 Performance Evidence categories
        - Each category should be substantial enough to warrant its own assessment item
        - CRITICAL: For PE1, ensure it includes the complete evidence overview AND all specific evidence requirements
        - CRITICAL: For Knowledge Evidence, extract ALL knowledge areas mentioned, including comprehensive lists and sub-categories

        QUALITY CHECKS:
        - Ensure all elements have corresponding performance criteria
        - Verify performance criteria numbering matches element structure
        - Check that descriptions are complete sentences, not fragments
        - Confirm all required sections are populated with real content
        - Verify PE1 is complete and includes all evidence requirements
        - Verify Knowledge Evidence includes all knowledge areas mentioned
        - For HLTWHS002: Ensure Element 5 and its performance criteria (5.1, 5.2, 5.3) are included

        Here is the training.gov.au page content to extract from:

        {page_content}

        IMPORTANT: Extract ALL content from the entire page. Do not stop early or skip any sections.
        If you see more elements, performance criteria, or evidence items, include them all.
        Pay special attention to PE1 - ensure it includes the complete evidence overview and all specific requirements.
        For HLTWHS002: Make sure to include Element 5 and all its performance criteria.

        Extract the complete structured data as valid JSON:
        """
        
        try:
            response = self._call_gemini_api(extraction_prompt)
            
            # Clean and parse JSON response
            json_response = self._clean_json_response(response)
            extracted_data = json.loads(json_response)
            
            # Validate the extracted data
            if not self._validate_extracted_data(extracted_data, uoc_code):
                raise ValueError("Extracted data failed validation")
            
            # Add metadata
            extracted_data.update({
                'fetched_at': datetime.now().isoformat(),
                'method': 'web_search_llm_extraction',
                'source_url': source_url,
                'extraction_quality': 'high' if len(extracted_data['elements']) > 1 else 'medium'
            })
            
            # Post-processing validation to check for missing elements
            self._validate_extraction_completeness(extracted_data, uoc_code, page_content)
            
            print(f"✅ Successfully extracted {uoc_code}:")
            print(f"   📋 Elements: {len(extracted_data['elements'])}")
            print(f"   📊 Performance Criteria: {len(extracted_data['performance_criteria'])}")
            print(f"   🎯 Performance Evidence: {len(extracted_data['performance_evidence'])}")
            print(f"   🧠 Knowledge Evidence: {len(extracted_data['knowledge_evidence'])}")
            
            return extracted_data
            
        except Exception as e:
            print(f"❌ LLM extraction error for {uoc_code}: {e}")
            return self._create_fallback_data(uoc_code, f"LLM extraction error: {e}")
    
    def _validate_extracted_data(self, data: Dict, uoc_code: str) -> bool:
        """Validate that extracted data has required structure and content"""
        
        required_fields = ['uoc_code', 'title', 'elements', 'performance_criteria', 
                          'performance_evidence', 'knowledge_evidence']
        
        # Check all required fields exist
        for field in required_fields:
            if field not in data:
                print(f"⚠️ Missing field: {field}")
                return False
        
        # Check UoC code matches
        if data['uoc_code'].upper() != uoc_code.upper():
            print(f"⚠️ UoC code mismatch: expected {uoc_code.upper()}, got {data['uoc_code']}")
            return False
        
        # Check we have actual content (not just placeholders)
        if len(data['elements']) == 0:
            print(f"⚠️ No elements extracted")
            return False
        
        # Check for placeholder text
        placeholder_indicators = ['[manual extraction needed]', '[click to edit]', 'placeholder']
        for element in data['elements']:
            desc = element.get('description', '').lower()
            if any(indicator in desc for indicator in placeholder_indicators):
                print(f"⚠️ Placeholder text detected in elements")
                return False
        
        # Additional LLM-based quality validation
        validation_prompt = f"""
        Please review this extracted UoC data for completeness and accuracy:

        {json.dumps(data, indent=2)}

        Check for:
        1. Are all performance criteria properly numbered (1.1, 1.2, 2.1, etc.)?
        2. Do performance criteria match the number of elements?
        3. Are descriptions complete sentences with professional VET language?
        4. Are there any obvious gaps or missing information?
        5. Does the content make sense for a {uoc_code} unit?

        Return either:
        - "VALID" if the data looks complete and accurate
        - "ISSUES: [specific problems found]" if there are quality concerns

        Focus on structural completeness rather than content expertise.
        """
        
        try:
            validation_response = self._call_gemini_api(validation_prompt)
            if "VALID" in validation_response.upper():
                print(f"✅ LLM validation passed for {uoc_code}")
                return True
            else:
                print(f"⚠️ LLM validation issues: {validation_response}")
                # Still accept the data but log the issue
                return True
        except Exception as e:
            print(f"⚠️ Validation check failed: {e}")
            # If validation fails, still accept the data but log the issue
            return True
        
        return True
    
    def _validate_extraction_completeness(self, extracted_data: Dict, uoc_code: str, page_content: str) -> None:
        """Post-processing validation to check for missing elements and evidence"""
        
        # Check for common patterns that suggest missing content
        issues = []
        
        # Check if we have a reasonable number of elements (most UoCs have 2-6 elements)
        if len(extracted_data.get('elements', [])) < 2:
            issues.append(f"Only {len(extracted_data.get('elements', []))} elements found - may be incomplete")
        
        # Check if performance criteria match element structure
        pcs = extracted_data.get('performance_criteria', [])
        if pcs:
            # Get the highest element number from performance criteria
            max_element = 0
            for pc in pcs:
                try:
                    element_num = int(pc.get('code', '0.0').split('.')[0])
                    max_element = max(max_element, element_num)
                except:
                    pass
            
            if max_element != len(extracted_data.get('elements', [])):
                issues.append(f"Performance criteria suggest {max_element} elements but only {len(extracted_data.get('elements', []))} found")
        
        # Check for missing evidence sections
        if not extracted_data.get('performance_evidence'):
            issues.append("No performance evidence found")
        
        # Check for appropriate Performance Evidence (should be broad categories, not granular)
        pe_items = extracted_data.get('performance_evidence', [])
        if len(pe_items) < 3:  # Should have 3-8 broad categories
            issues.append(f"Only {len(pe_items)} performance evidence categories found - may be incomplete")
        elif len(pe_items) > 10:  # Too granular
            issues.append(f"Too many performance evidence items ({len(pe_items)}) - should be broader categories")
        
        if not extracted_data.get('knowledge_evidence'):
            issues.append("No knowledge evidence found")
        
        # Check for appropriate Knowledge Evidence (should be broad categories, not granular)
        ke_items = extracted_data.get('knowledge_evidence', [])
        if len(ke_items) < 5:  # Should have 5-12 broad categories
            issues.append(f"Only {len(ke_items)} knowledge evidence categories found - may be incomplete")
        elif len(ke_items) > 15:  # Too granular
            issues.append(f"Too many knowledge evidence items ({len(ke_items)}) - should be broader categories")
        
        # If issues found, try to re-extract with a focused prompt
        if issues:
            print(f"⚠️ Potential extraction issues for {uoc_code}: {', '.join(issues)}")
            
            # Try a focused re-extraction for missing elements
            if len(extracted_data.get('elements', [])) < 4:  # Most UoCs have 2-6 elements
                print(f"🔄 Attempting focused re-extraction for {uoc_code}...")
                focused_data = self._focused_re_extraction(uoc_code, page_content, extracted_data)
                if focused_data:
                    # Merge the focused extraction with original data
                    extracted_data.update(focused_data)
                    print(f"✅ Re-extraction completed for {uoc_code}")
    
    def _focused_re_extraction(self, uoc_code: str, page_content: str, original_data: Dict) -> Optional[Dict]:
        """Attempt focused re-extraction for missing elements"""
        
        focus_prompt = f"""
        I need to check if there are any missing elements or evidence items for {uoc_code}.
        
        Current extraction has:
        - {len(original_data.get('elements', []))} elements
        - {len(original_data.get('performance_criteria', []))} performance criteria
        - {len(original_data.get('performance_evidence', []))} performance evidence items
        - {len(original_data.get('knowledge_evidence', []))} knowledge evidence items
        
        Please scan the page content again and look for:
        1. Any additional elements (especially if you see numbered elements like 4, 5, 6)
        2. Any missing performance criteria
        3. Any missing performance evidence items (group into broad, assessable categories)
        4. Any missing knowledge evidence items (group into broad, assessable categories - ignore introductory phrases)
        
        REMEMBER: For KE and PE, be INTELLIGENT - group related concepts into meaningful categories, don't be granular.
        
        Return ONLY a JSON object with any missing items you find:
        {{
            "elements": [{{"id": "4", "description": "..."}}],
            "performance_criteria": [{{"code": "4.1", "description": "..."}}],
            "performance_evidence": [{{"code": "PE6", "description": "..."}}],
            "knowledge_evidence": [{{"code": "KE9", "description": "..."}}]
        }}
        
        If no missing items found, return: {{}}
        
        Page content to check:
        {page_content}
        """
        
        try:
            response = self._call_gemini_api(focus_prompt)
            json_response = self._clean_json_response(response)
            focused_data = json.loads(json_response)
            
            # Only return if we found additional content
            if any(focused_data.values()):
                return focused_data
                
        except Exception as e:
            print(f"⚠️ Focused re-extraction failed: {e}")
        
        return None
    
    def _call_gemini_api(self, prompt: str) -> str:
        """Make API call to Gemini with rate limiting"""
        
        # Basic rate limiting to prevent API quota exhaustion
        time.sleep(0.5)
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Low temperature for consistent extraction
                "maxOutputTokens": 4000,  # Increased for comprehensive extraction
                "topP": 0.8,
                "topK": 10
            }
        }
        
        url = f"{self.gemini_endpoint}?key={self.gemini_api_key}"
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract valid JSON"""
        
        # Remove markdown code blocks if present
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*$', '', response, flags=re.MULTILINE)
        
        # Find JSON object boundaries
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start != -1 and end > start:
            json_str = response[start:end]
            
            # Basic JSON cleanup
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
            
            return json_str
        
        raise ValueError("No valid JSON found in LLM response")
    
    def _get_cached_data(self, uoc_code: str) -> Optional[Dict]:
        """Check if we have valid cached data for this UoC"""
        cache_file = os.path.join(self.cache_dir, f"{uoc_code.upper()}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            # Don't use cached data if it's fallback/mock data
            if cached['data'].get('requires_manual_entry', False) or cached['data'].get('method') == 'fallback':
                print(f"🔄 Ignoring cached fallback data for {uoc_code}, fetching fresh data...")
                return None
            
            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cached['cached_at'])
            if datetime.now() - cached_time < self.cache_duration:
                # Ensure proper numbering for cached data
                return self._ensure_proper_numbering(cached['data'])
            else:
                print(f"🕐 Cache expired for {uoc_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ Error reading cache for {uoc_code}: {e}")
            return None
    
    def _cache_data(self, uoc_code: str, data: Dict) -> None:
        """Save UoC data to cache"""
        cache_file = os.path.join(self.cache_dir, f"{uoc_code.upper()}.json")
        
        cache_entry = {
            'uoc_code': uoc_code.upper(),
            'cached_at': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)
            print(f"💾 Cached data for {uoc_code}")
        except Exception as e:
            print(f"⚠️ Error caching data for {uoc_code}: {e}")
    
    def _create_fallback_data(self, uoc_code: str, error_msg: str) -> Dict:
        """Create fallback data structure with manual entry template"""
        
        return {
            'uoc_code': uoc_code.upper(),
            'title': f'Unit of Competency {uoc_code.upper()} - Manual entry required',
            'elements': [
                {'id': '1', 'description': f'[Manual entry needed] Visit training.gov.au to get Element 1 for {uoc_code.upper()}'},
                {'id': '2', 'description': f'[Manual entry needed] Visit training.gov.au to get Element 2 for {uoc_code.upper()}'}
            ],
            'performance_criteria': [
                {'code': '1.1', 'description': '[Manual entry needed] Performance criteria 1.1'},
                {'code': '1.2', 'description': '[Manual entry needed] Performance criteria 1.2'}
            ],
            'performance_evidence': [
                {'code': 'PE1', 'description': '[Manual entry needed] Performance evidence requirement'}
            ],
            'knowledge_evidence': [
                {'code': 'KE1', 'description': '[Manual entry needed] Knowledge evidence requirement'}
            ],
            'error': error_msg,
            'fetched_at': datetime.now().isoformat(),
            'requires_manual_entry': True,
            'method': 'fallback',
            'manual_entry_url': f'https://training.gov.au/training/details/{uoc_code.upper()}/unitdetails'
        }
    
    def _ensure_proper_numbering(self, uoc_data: Dict) -> Dict:
        """Ensure all components have proper numbering (E1, PC1.1, PE1, KE1)"""
        
        # Ensure elements have proper E prefix
        if 'elements' in uoc_data:
            for i, element in enumerate(uoc_data['elements'], 1):
                if 'id' in element:
                    # Ensure element ID is in correct format
                    element_id = element['id']
                    if not element_id.startswith('E'):
                        element['id'] = f"E{element_id}"
                else:
                    element['id'] = f"E{i}"
        
        # Ensure performance criteria have proper PC prefix
        if 'performance_criteria' in uoc_data:
            for pc in uoc_data['performance_criteria']:
                if 'code' in pc:
                    code = pc['code']
                    if not code.startswith('PC'):
                        pc['code'] = f"PC{code}"
        
        # Ensure performance evidence has proper PE prefix
        if 'performance_evidence' in uoc_data:
            for i, pe in enumerate(uoc_data['performance_evidence'], 1):
                if 'code' in pe:
                    code = pe['code']
                    if not code.startswith('PE'):
                        pe['code'] = f"PE{code}"
                else:
                    pe['code'] = f"PE{i}"
        
        # Ensure knowledge evidence has proper KE prefix
        if 'knowledge_evidence' in uoc_data:
            for i, ke in enumerate(uoc_data['knowledge_evidence'], 1):
                if 'code' in ke:
                    code = ke['code']
                    if not code.startswith('KE'):
                        ke['code'] = f"KE{code}"
                else:
                    ke['code'] = f"KE{i}"
        
        return uoc_data
    
    def clear_cache(self, uoc_code: str = None) -> bool:
        """Clear cache for specific UoC or all cache"""
        try:
            if uoc_code:
                # Clear specific UoC cache
                cache_file = os.path.join(self.cache_dir, f"{uoc_code.upper()}.json")
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    print(f"🗑️  Cleared cache for {uoc_code}")
                    return True
                else:
                    print(f"⚠️  No cache found for {uoc_code}")
                    return False
            else:
                # Clear all cache
                import glob
                cache_files = glob.glob(os.path.join(self.cache_dir, "*.json"))
                for cache_file in cache_files:
                    os.remove(cache_file)
                print(f"🗑️  Cleared all cache ({len(cache_files)} files)")
                return True
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
            return False

# Test function
def test_web_search_fetch_agent():
    """Test the WebSearchFetchAgent"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key or api_key == 'your-gemini-api-key-here':
        print("❌ Please set GEMINI_API_KEY environment variable")
        print("Get your key from: https://aistudio.google.com/app/apikey")
        return None
    
    print("🧪 Testing WebSearchFetchAgent...")
    
    agent = FetchAgent(api_key)
    
    # Test with a known UoC
    test_uoc = "HLTINF006"
    print(f"\n🔍 Testing with {test_uoc}...")
    
    result = agent.execute(test_uoc)
    
    print(f"\n📊 Results for {test_uoc}:")
    print(f"Title: {result['title']}")
    print(f"Elements: {len(result['elements'])}")
    print(f"Performance Criteria: {len(result['performance_criteria'])}")
    print(f"Performance Evidence: {len(result['performance_evidence'])}")
    print(f"Knowledge Evidence: {len(result['knowledge_evidence'])}")
    print(f"Method: {result.get('method', 'unknown')}")
    
    if result.get('error'):
        print(f"⚠️ Error: {result['error']}")
    
    # Show first few elements as example
    if result['elements']:
        print(f"\n📋 Sample Elements:")
        for i, element in enumerate(result['elements'][:2]):
            print(f"  {element['id']}: {element['description']}")
    
    return result

if __name__ == "__main__":
    test_web_search_fetch_agent() 