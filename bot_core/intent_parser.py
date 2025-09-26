import re

def parse_intent(user_input):
    text = user_input.lower()
    nums = re.findall(r"\d+", text)
    if "block" in text:
        if len(nums) >= 3:
            return "block", nums[:3]
        return "block", ["100", "100", "50"]
    elif "extrude" in text:
        if len(nums) >= 2:
            return "extrude", nums[:2]
        return "extrude", ["50", "10"]
    elif "fillet" in text:
        if len(nums) >= 1:
            return "fillet", nums[:1]
        return "fillet", ["5"]
    elif "unite" in text:
        return "unite", []
    elif "extract" in text:
        return "extract_region", []
    else:
        return "unknown", []
