from seleniumbase import sb_cdp
from playwright.sync_api import sync_playwright
from groq import Groq
import tools
import json

sb = sb_cdp.Chrome(locale="de")
endpoint_url = sb.get_endpoint_url()

systemPrompt = """You are a browser automation agent. 

IMPORTANT RULES:
- ALWAYS call get_state first before clicking or typing anything
- NEVER guess selectors
- Only use selectors that you got from get_state
"""


def cookieBanner(page):
   for text in ["Akzeptieren", "Accept", "Accept all", "Alle akzeptieren", "Zustimmen", "I agree"]:
        try:
            page.locator(f"button:has-text('{text}')").click(timeout=1000)
            page.wait_for_timeout(500)
            return
        except:
            pass
        
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
            tool_choice="auto"
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

        if name == "open_site":
            waitForPage(page)

        if name == "click":
            page.wait_for_timeout(1000)
            cookieBanner(page)

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

    main("Open Youtube search for Fornite videos and open the first video to show", page)  
    input("closed")