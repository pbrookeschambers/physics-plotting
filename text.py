import re
from typing import List

prefixes = {
    "kilo": "k",
    "mega": "M",
    "giga": "G",
    "tera": "T",
    "peta": "P",
    "exa": "E",
    "centi": "c",
    "milli": "m",
    "micro": "µ",
    "nano": "n",
    "pico": "p",
}

units = {
    "metre": "m",
    "meter": "m",
    "gram": "g",
    "second": "s",
    "ampere": "A",
    "kelvin": "K",
    "mole": "mol",
    "candela": "cd",
    "hertz": "Hz",
    "newton": "N",
    "pascal": "Pa",
    "joule": "J",
    "watt": "W",
    "coulomb": "C",
    "volt": "V",
    "farad": "F",
    "ohm": "Ω",
    "siemens": "S",
    "weber": "Wb",
    "tesla": "T",
    "henry": "H",
    "degree celsius": "°C",
    "lumen": "lm",
    "lux": "lx",
    "becquerel": "Bq",
    "electron volt": "eV",
    "degree": "°",
    "radian": "rad",
}

powers = {
    "squared": 2,
    "cubed": 3,
}

def parse_unit(unit: str, add_space: bool = True) -> str:
    per = False
    unit_dict = {}
    while len(unit) > 0:
        current_prefix = ""
        current_unit = None
        if unit.startswith("per"):
            per = True
            unit = unit[3:].lstrip()
            continue
        for prefix in prefixes:
            if unit.startswith(prefix):
                current_prefix = prefixes[prefix]
                unit = unit[len(prefix):].lstrip()
                break
        for unit_name in units:
            if unit.startswith(unit_name):
                current_unit = units[unit_name]
                unit = unit[len(unit_name):].lstrip()
                break
        else:
            raise ValueError(f"Unrecognised unit: {unit}")
        current_power = 1
        for power in powers:
            if unit.startswith(power):
                current_power = powers[power]
                unit = unit[len(power):].lstrip()
                break
        if current_prefix + current_unit in unit_dict:
            unit_dict[current_prefix + current_unit] += -current_power if per else current_power
        else:
            unit_dict[current_prefix + current_unit] = -current_power if per else current_power
    unit_out = ""
    # split the dictionary into positive and negative powers
    positive_powers = {}
    negative_powers = {}
    for unit in unit_dict:
        if unit_dict[unit] > 0:
            positive_powers[unit] = unit_dict[unit]
        elif unit_dict[unit] < 0:
            negative_powers[unit] = unit_dict[unit]
        # we get rid of units with power 0 for free here
    # sort the positive powers, smallest to largest
    positive_powers = dict(sorted(positive_powers.items(), key=lambda item: item[1]))
    # sort the negative powers, largest to smallest
    negative_powers = dict(sorted(negative_powers.items(), key=lambda item: item[1], reverse=True))
    # add the positive powers to the string
    unit_out += "\,".join([
        fr"\text{{{unit}}}" + (f"^{power}" if power != 1 else "") for unit, power in positive_powers.items()
    ])
    # add the negative powers to the string
    if len(unit_out) > 0 and len(negative_powers) > 0:
        unit_out += "\,"
    unit_out += "\,".join([
        fr"\text{{{unit}}}^{{{power}}}" for unit, power in negative_powers.items()
    ])
    return ("~" if add_space else "") + "\\ensuremath{" + unit_out + "}"



        

def process_units(text: str) -> str:
    # search for any text which matches the pattern "unit{.*?}"
    # process the units to appropriate latex code
    # replace the text with the processed text
    # return the processed text

    pattern = r"unit\{(.*?)\}"
    
    for match in re.finditer(pattern, text):
        # was the character before the unit (ignoring whitespace) a (?
        # if so, we don't want to add a space
        add_space = True
        if match.start() > 0 and text[:match.start()].rstrip()[-1] in ["(", "[", "="]:
            add_space = False
        unit = parse_unit(match.group(1).strip(), add_space=add_space)
        text = text.replace(match.group(0), unit)
    return text

def process_fit(text: str, fit_params: List[float]) -> str:
    # parameter names are always "a", "b", etc. Create a dictionary mapping these to the fit parameters
    params = {}
    for i, param in enumerate(fit_params):
        params[chr(ord("a") + i)] = param
    # text will have {} for normal latex. Need to replace those with double braces. Actual fit parameters will be fit{...}
    # temporarily replace fit parameters with fit(...), then replace the braces, then replace fit(...) with the actual fit parameters ready for format
    text = re.sub("fit\{(.*?)\}", r"fit(\1)", text)
    text = text.replace("{", "{{").replace("}", "}}")
    text = text.replace("fit(", "{").replace(")", "}")
    text = text.format(**params)
    return text