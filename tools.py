
def click(page, text):
    try:
        locator = page.get_by_text(text, exact=True).first
        locator.scroll_into_view_if_needed()
        locator.click()
    except:
        try:
            locator = page.get_by_text(text, exact=False).first
            locator.scroll_into_view_if_needed()
            locator.click()
        except:
            page.locator(f"text={text}").first.evaluate("el => el.click()")
def type_text(page, selector, value):
    page.locator(selector).first.fill(value)

def press_enter(page, selector):
    page.locator(selector).first.press("Enter")

def open_site(page, url):
   page.goto(url)

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
            type_ = el.get_attribute("type")


            if name:
                selector = f"{tag}[name='{name}']"
            elif id_:
                selector = f"#{id_}"
            elif aria_label:
                selector = f"{tag}[aria-label='{aria_label}']"
            elif placeholder:
                selector = f"{tag}[placeholder='{placeholder}']"
            else:
                continue

            result.append({
                "selector": selector,
                "type": type_,
                "placeholder": placeholder,
                "title": el.get_attribute("title"),  
            })
        except:
            pass

    return result

def executeTool(name, args, page):
    if name == "click":
      click(page, args["text"])
    elif name == "type_text":
      type_text(page, args["selector"], args["text"])
    elif name == "press_enter":
      press_enter(page, args["selector"])
    elif name == "open_site":
      open_site(page,args["url"])
    elif name == "get_state":
        return get_state(page, args["element_type"])
       

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