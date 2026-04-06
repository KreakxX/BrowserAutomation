def click(page, text):
    methods = [
        lambda: page.get_by_text(text, exact=True).first.click(timeout=1000),
        lambda: page.get_by_text(text, exact=False).first.click(timeout=1000),
        lambda: page.locator(f"[aria-label='{text}']").first.click(timeout=1000),
        lambda: page.locator(f"[title='{text}']").first.click(timeout=1000),
        lambda: page.locator(f"[aria-label*='{text}']").first.click(timeout=1000),
        lambda: page.locator(f"text={text}").first.evaluate("el => el.click()"),
    ]
    
    for method in methods:
        try:
            method()
            return "success"
        except:
            continue
    
    return "failed - element not found. Call get_state with a different element_type."
 
def type_text(page, selector, value):
    page.locator(selector).first.fill(value)

def press_enter(page, selector):
    page.locator(selector).first.press("Enter")

def open_site(page, url):
   page.goto(url)

def get_content(page):
    locators = page.locator("p, h1, h2, h3").all()
    content = [];
    for el in locators:
       text_content = el.inner_text().strip() if el.inner_text() else None
       content.append(text_content)
    return content;

def open_tab(context,url):
    newPage = context.new_page()
    newPage.goto(url)
    return newPage


def close_tab(context, index):
    print("test")

def switch_tab(context, index):
    return context.pages[index]


def scrape_site(page):
    locators = page.locator("button, a, input, textarea, select, p, h1, h2, h3, span").all()
    return locators;


def get_state(page, element_type):
    if element_type == "button":
        locators = page.locator("button").all()
    elif element_type == "input":
        locators = page.locator("input, textarea").all()
    elif element_type == "link":
        locators = page.locator("a").all()   
    else:
        locators = page.locator(element_type).all()

    result = []
    for el in locators:
        try:
            if not el.is_visible():
                continue

            tag = el.evaluate("el => el.tagName.toLowerCase()")
            name = el.get_attribute("name")
            id_ = el.get_attribute("id")
            placeholder = el.get_attribute("placeholder")
            aria_label = el.get_attribute("aria-label")
            text_content = el.inner_text().strip()[:80] if el.inner_text() else None


            if name:
                selector = f"{tag}[name='{name}']"
            elif id_:
                selector = f"#{id_}"
            elif aria_label:
                selector = f"{tag}[aria-label='{aria_label}']"
            elif placeholder:
                selector = f"{tag}[placeholder='{placeholder}']"
            elif text_content:
              selector = f"{tag}:has-text('{text_content}')"
            else:
                continue

            result.append({
                "selector": selector,
                "text": text_content
            })
        except:
            pass
    if element_type == "link":
        result = [el for el in result if el.get("text") and len(el.get("text", "")) > 3]

    return result

def executeTool(name, args, page, context):
    if name == "click":
      return click(page, args["text"])
    elif name == "type_text":
      type_text(page, args["selector"], args["text"])
    elif name == "press_enter":
      press_enter(page, args["selector"])
    elif name == "open_site":
      open_site(page,args["url"])
    elif name == "get_state":
        return get_state(page, args["element_type"])
    elif name == "get_content":
        return get_content(page);
    elif name == "scrape_site":
        return scrape_site(page)
    elif name == "open_tab":
        return open_tab(context, args["url"])
    elif name == "switch_tab":
        return switch_tab(context, args["index"]);
       

tools = [
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click a button by visible text",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type into an input field",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "text": {"type": "string"}
                },
                "required": ["selector", "text"]
            }
        }
    },
       {
        "type": "function",
        "function": {
            "name": "press_enter",
            "description": "Hit Enter to submit a form or search",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector of the element"}
                },
                "required": ["selector"]
            }
        }
    },
     {
        "type": "function",
        "function": {
            "name": "open_site",
            "description": "Open a Website",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "the url to open"},
                },
                "required": ["url"]
            }
        }
    },
 {
        "type": "function",
        "function": {
            "name": "switch_tab",
            "description": "Switches to another tab",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "number", "description": "the index of the tab"},
                },
                "required": ["index"]
            }
        }
    },

     {
        "type": "function",
        "function": {
            "name": "open_tab",
            "description": "Open a new Tab",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "the url to open in the new Tab"},
                },
                "required": ["url"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_content",
            "description": "get the Content of a Page",
            "parameters": {
                "type": "object",
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_site",
            "description": "Gets everything from a site, only use this when specifically asked for",
            "parameters": {
                "type": "object",
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "get_state",
        "description": "Get all elements of a specific type on the page to find the right selector",
        "parameters": {
            "type": "object",
            "properties": {
                "element_type": {
                    "type": "string",
                    "enum": ["button", "input", "link"],
                    "description": "Type of elements to get"
                }
            },
            "required": ["element_type"]
        }
    }
}
   
]