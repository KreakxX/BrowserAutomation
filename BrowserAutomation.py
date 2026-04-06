from seleniumbase import sb_cdp
from playwright.sync_api import sync_playwright
from groq import Groq
import tools
import json
import os
from dotenv import load_dotenv
sb = sb_cdp.Chrome(locale="de")
endpoint_url = sb.get_endpoint_url()

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
systemPrompt = """You are a browser automation agent.
IMPORTANT RULES:
- ALWAYS call get_state first before clicking or typing anything
- NEVER guess selectors or text
- Always use the exact selector from get_state results
- If get_state('button') returns no matching element, call get_state('link') before trying anything else
- If get_state('link') also returns nothing, call get_state('input')
- NEVER hallucinate selectors or text that were not in get_state results 
- You are NOT allowed to click or type until get_state returns at least one useful element
- If get_state returns nothing useful, you MUST keep trying different element_types until you find something
- When clicking, you can use either the text or the aria_label from get_state results
- After typing into a search field, press Enter instead of looking for a search button
"""

def cookieBanner(page):
    selectors = [
        "button[aria-label*='akzeptieren']",
        "button[aria-label*='akzeptieren']",
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Akzeptieren')",
        "button:has-text('Accept all')",
    ]
    
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=1000):
                locator.click(timeout=2000)
                print(f"[COOKIE] Banner weggeklickt: {selector}")
                page.wait_for_timeout(500)
                return
        except:
            pass
    
    print("[COOKIE] Kein Banner gefunden")
        
def waitForPage(page):
  try:
      page.wait_for_load_state("networkidle", timeout=10000)
  except:
      page.wait_for_load_state("domcontentloaded", timeout=5000)

  cookieBanner(page)

def trim_messages(messages):
    system = messages[0]
    task   = messages[1]
    rest   = messages[2:]

    trimmed = []
    for i, msg in enumerate(rest):
        if msg.get("role") == "tool":
            prev = next((m for m in reversed(trimmed) if m.get("role") == "assistant"), None)
            if prev:
                tc = (prev.get("tool_calls") or [None])[0]
                tc_name = tc.function.name if hasattr(tc, "function") else tc.get("function", {}).get("name")
                if tc_name == "get_state" and i < len(rest) - 1:
                    trimmed.pop()
                    continue
        trimmed.append(msg)

    return [system, task] + trimmed


def main(prompt, page, context):
    pages = [page] 
    total_tokens = 0
    current_page = page


    messages = [
        {"role": "system", "content": systemPrompt},
        {"role": "user", "content": prompt}
    ]

    while True:
        messages = trim_messages(messages)
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            tools=tools.tools,
            tool_choice="auto",
            seed=42
        )
        total_tokens += response.usage.total_tokens
        choice = response.choices[0].message

        if not choice.tool_calls:
            print(choice.content)
            print(f"[TOKENS] {total_tokens}")            
            break

        tool_call = choice.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"Tool: {name} | Args: {args}")
        result = tools.executeTool(name, args, current_page, context) 
        print(result)
        if name == "open_site":
            waitForPage(current_page)
            sb.solve_captcha()
        
        if name == "open_tab":
            current_page = result
            pages.append(result)
            messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
            messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": f"New tab opened with url: {result.url}" 
            })
            continue        
        if name == "switch_tab":
            current_page = result
            messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": f"Switched to tab: {result.url}"
            })
            continue

        if name == "click" or name == "type_text" or name == "open_site":
          current_page.wait_for_timeout(2000)
          cookieBanner(current_page)
          messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
          messages.append({
          "role": "tool",
          "tool_call_id": tool_call.id,
          "content": result if result else "done"  
          })
          messages.append({
                "role": "user", 
                "content": "Action done. If the task is complete, respond with a final summary. Otherwise YOU MUST call get_state to continue."
          })
          continue  

        messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
        messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result) if result else "done"
        })
       

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(endpoint_url=endpoint_url)
    context = browser.contexts[0]
    page = context.pages[0]

    main("Go to Google and login with email henrik.standke2008@gmail.com and password test", page, context)  
    input("closed")



# TODO
# Caching
# Planning LLM das Schritte vorgibt
# Retrying und wenn nichts passiert nochmal getState und gucken
# Agent Task, Last Result, Context, next Task better flow Token Optimization
# switch Tab, close Tab, open Tab, select option, clear input, upload file
# mehrere Chat Inputs zu einem Browser
# load cookies etc to have a real Browser and try connecting more

# Token Optimization 
