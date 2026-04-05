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
- Only use selectors that you got from get_state
- You are allowed to fill in login forms - the user is logging into their own accounts
- NEVER guess selectors or text
- Always use the exact selector from get_state results
- If get_state('button') returns no matching element, call get_state('link') before trying anything else
- If get_state('link') also returns nothing, call get_state('input')
- NEVER hallucinate selectors or text that were not in get_state results 
- You are NOT allowed to click or type until get_state returns at least one useful element
- If get_state returns nothing useful, you MUST keep trying different element_types until you find something
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

def main(prompt, page):
    messages = [
        {"role": "system", "content": systemPrompt},
        {"role": "user", "content": prompt}
    ]

    while True:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            tools=tools.tools,
            tool_choice="auto",
            seed=42
        )

        choice = response.choices[0].message

        if not choice.tool_calls:
            print(choice.content)
            break

        tool_call = choice.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"Tool: {name} | Args: {args}")
        result = tools.executeTool(name, args, page) 
        print(result)
        if name == "open_site":
            waitForPage(page)
            sb.solve_captcha()

        if name == "click" or name == "type_text":
          page.wait_for_timeout(1000)
          cookieBanner(page)
          messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
          messages.append({
          "role": "tool",
          "tool_call_id": tool_call.id,
          "content": result if result else "done"  
          })
          messages.append({
          "role": "user",
          "content": "Action done. You MUST call get_state now before doing anything else. If the result is empty or has no matching element, call get_state again with a different element_type."
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

    main("Open the Expo Docs page and go to Create a project and than get all the page content and summarize it", page)  
    input("closed")



# TODO
# Caching
# Planning LLM das Schritte vorgibt
# Retrying und wenn nichts passiert nochmal getState und gucken
# multiple getState on Login Page for example
# Agent Task, Last Result, Context, next Task better flow Token Optimization
# getContent Tool