#!/usr/bin/env python3
"""
HA Voice Training Dataset Generator
Generuje training vzorky pro fine-tuning Llama modelu
"""

import json
import random
import os
from typing import Dict, List, Any, Tuple, Optional


def load_json(filepath: str) -> Dict:
    """Načte JSON soubor"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_jsonl(data: List[Dict], filepath: str):
    """Uloží data do JSONL formátu"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def generate_entity_pool() -> Dict[str, List[str]]:
    """
    Vygeneruje realistický pool entit simulující skutečný HA setup
    """
    locations = ['kuchyn', 'obyvak', 'loznice', 'koupelna', 'chodba', 'garaz', 'dilna']
    
    entities = {
        'light': [],
        'climate': [],
        'cover': [],
        'switch': [],
        'fan': [],
        'input_boolean': [],
        'input_number': []
    }
    
    # Světla
    for loc in locations:
        entities['light'].extend([
            f'light.{loc}_strop',
            f'light.{loc}_led'
        ])
    
    # Climate (topení) - jen v hlavních místnostech
    for loc in ['kuchyn', 'obyvak', 'loznice', 'koupelna']:
        entities['climate'].append(f'climate.{loc}_topeni')
    
    # Covers (žaluzie)
    for loc in ['kuchyn', 'obyvak', 'loznice']:
        entities['cover'].append(f'cover.{loc}_zalousie')
    
    # Switches
    entities['switch'].extend([
        'switch.garaz_vrata',
        'switch.zahrada_cerpadlo',
        'switch.dilna_ventilator'
    ])
    
    # Fans
    entities['fan'].extend([
        'fan.obyvak_ventilator',
        'fan.loznice_ventilator',
        'fan.koupelna_odtah'
    ])
    
    # Input booleans
    entities['input_boolean'].extend([
        'input_boolean.rezim_dovolena',
        'input_boolean.bojler',
        'input_boolean.automatizace_topeni'
    ])
    
    # Input numbers
    entities['input_number'].extend([
        'input_number.bojler_teplota',
        'input_number.topeni_limit',
        'input_number.intenzita_svetla_default'
    ])
    
    return entities


def extract_location_from_instruction(instruction: str) -> Optional[str]:
    """
    Extrahuje lokaci z instrukce
    Returns: normalized location key nebo None
    """
    instruction_lower = instruction.lower()
    
    locations_map = {
        'kuchyn': ['kuchyni', 'kuchyně', 'kuchyň'],
        'obyvak': ['obýváku', 'obývacím', 'obývák', 'obyvaku'],
        'loznice': ['ložnici', 'ložnice', 'loznici'],
        'koupelna': ['koupelně', 'koupelna', 'koupelne'],
        'chodba': ['chodbě', 'chodba', 'chodbe'],
        'garaz': ['garáži', 'garáž', 'garazi', 'garaz'],
        'dilna': ['dílně', 'dílna', 'dilne', 'dilna'],
        'zahrada': ['zahradě', 'zahrada', 'zahrade']
    }
    
    for loc_key, loc_variants in locations_map.items():
        if any(variant in instruction_lower for variant in loc_variants):
            return loc_key
    
    return None


def match_entities_by_location(entities: List[str], location: str) -> List[str]:
    """
    Filtruje entity podle lokace
    """
    return [e for e in entities if location in e.lower()]


def create_entity_list(all_entities: Dict[str, List[str]], target_domain: str, target_entity: str = None) -> Dict[str, List[str]]:
    """
    Vytvoří realistický entity list pro model
    """
    entity_list = {}
    
    # Přidej target domain
    domain_entities = all_entities[target_domain].copy()
    random.shuffle(domain_entities)
    entity_list[target_domain] = domain_entities[:8]
    
    # Ujisti se že target entita je v listu (pokud je specifikovaná)
    if target_entity and target_entity not in entity_list[target_domain]:
        entity_list[target_domain].insert(random.randint(0, len(entity_list[target_domain])), target_entity)
    
    # Přidej pár dalších domén pro kontext
    other_domains = [d for d in all_entities.keys() if d != target_domain]
    num_other = random.randint(1, 3)
    for other_domain in random.sample(other_domains, min(num_other, len(other_domains))):
        other_entities = all_entities[other_domain].copy()
        random.shuffle(other_entities)
        entity_list[other_domain] = other_entities[:random.randint(2, 5)]
    
    return entity_list


def get_service_parameters(domain: str, service: str, combo: Dict, services_config: Dict) -> Dict:
    """
    Extrahuje parametry pro service call z konfigurace
    """
    params = {}
    
    # Najdi kombinaci v services config
    combo_params = combo.get('params', {})
    
    for param_name, param_config in combo_params.items():
        param_type = param_config.get('type')
        
        if param_type == 'choice':
            # Vyber náhodnou hodnotu ze seznamu
            values = param_config.get('values', [])
            if values:
                params[param_name] = random.choice(values)
        
        elif param_type == 'fixed':
            # Použij fixed hodnotu
            params[param_name] = param_config.get('value')
        
        elif param_type == 'relative':
            # Pro relative - jen označíme že vyžaduje get_state
            # Hodnotu vygenerujeme později
            pass
    
    return params


def generate_execute_sample(
    domain: str,
    service: str,
    combo: Dict,
    phrases: Dict,
    all_entities: Dict[str, List[str]],
    services_config: Dict
) -> Optional[Dict]:
    """
    Generuje EXECUTE SERVICE sample
    """
    # Vyber náhodnou frázi
    service_phrases = phrases.get(domain, {}).get(service, {})
    if not service_phrases:
        return None
    
    phrase_category = random.choice(list(service_phrases.keys()))
    phrase_template = random.choice(service_phrases[phrase_category])
    
    # Vyplň instruction
    instruction = phrase_template
    
    # Extrahuj lokaci pokud je v instrukci
    location_in_instruction = extract_location_from_instruction(instruction)
    
    # Nahraď location placeholder
    if '{location}' in instruction:
        location = random.choice(phrases.get('locations', ['v kuchyni', 'v obýváku', 'v ložnici']))
        instruction = instruction.replace('{location}', location)
        location_in_instruction = extract_location_from_instruction(instruction)
    
    # Vyber target entitu podle lokace
    available_entities = all_entities[domain]
    
    if location_in_instruction:
        # Filtruj podle lokace
        location_matches = match_entities_by_location(available_entities, location_in_instruction)
        
        if not location_matches:
            # Lokace neexistuje → vrátíme None, zkusíme jiný sample
            return None
        
        target_entity = random.choice(location_matches)
    else:
        # Žádná lokace → vyber náhodnou entitu
        target_entity = random.choice(available_entities)
    
    # Získej parametry ze service config
    params = get_service_parameters(domain, service, combo, services_config)
    
    # Nahraď placeholdery v instrukci a přidej do params
    if '{brightness}' in instruction:
        if 'brightness_pct' not in params:
            params['brightness_pct'] = random.choice([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        instruction = instruction.replace('{brightness}', str(params['brightness_pct']))
    
    if '{temperature}' in instruction:
        if 'temperature' not in params:
            params['temperature'] = random.choice([18, 19, 20, 21, 22, 23, 24, 25, 26])
        instruction = instruction.replace('{temperature}', str(params['temperature']))
    
    if '{position}' in instruction:
        if 'position' not in params:
            params['position'] = random.choice([0, 10, 25, 50, 75, 90, 100])
        instruction = instruction.replace('{position}', str(params['position']))
    
    if '{percentage}' in instruction:
        if 'percentage' not in params:
            params['percentage'] = random.choice([25, 50, 75, 100])
        instruction = instruction.replace('{percentage}', str(params['percentage']))
    
    if '{value}' in instruction:
        if 'value' not in params:
            params['value'] = random.choice([40, 45, 50, 55, 60, 65, 70, 75, 80])
        instruction = instruction.replace('{value}', str(params['value']))
    
    # Placeholder pro typy
    if '{switch_type}' in instruction:
        switch_type = random.choice(phrases.get('switch_types', ['vypínač']))
        instruction = instruction.replace('{switch_type}', switch_type)
    
    if '{boolean_name}' in instruction:
        bool_name = random.choice(phrases.get('boolean_types', ['režim dovolená']))
        instruction = instruction.replace('{boolean_name}', bool_name)
    
    if '{number_name}' in instruction:
        num_name = random.choice(phrases.get('number_names', ['teplotu']))
        instruction = instruction.replace('{number_name}', num_name)
    
    if '{name}' in instruction:
        instruction = instruction.replace('{name}', '')
    
    # Vytvoř entity list
    entity_list = create_entity_list(all_entities, domain, target_entity)
    
    # Vytvoř output
    output = {
        'action': 'execute_service',
        'service': f'{domain}.{service}',
        'data': {'entity_id': target_entity}
    }
    
    # Přidej parametry
    if params:
        output['data'].update(params)
    
    return {
        'instruction': instruction.strip(),
        'entities': entity_list,
        'output': output
    }


def generate_clarify_sample(
    domain: str,
    service: str,
    phrases: Dict,
    all_entities: Dict[str, List[str]]
) -> Optional[Dict]:
    """
    Generuje CLARIFY sample (nejasný příkaz → model se ptá)
    """
    service_phrases = phrases.get(domain, {}).get(service, {})
    if not service_phrases:
        return None
    
    # Hledej kategorii bez location
    generic_categories = [
        k for k in service_phrases.keys() 
        if 'without_location' in k or 'generic' in k or 'simple' in k
    ]
    
    if not generic_categories:
        generic_categories = list(service_phrases.keys())
    
    phrase_category = random.choice(generic_categories)
    phrase_template = random.choice(service_phrases[phrase_category])
    
    # Odeber všechny placeholdery
    instruction = phrase_template
    for placeholder in ['{location}', '{brightness}', '{temperature}', '{position}', 
                       '{percentage}', '{value}', '{switch_type}', '{boolean_name}', 
                       '{number_name}', '{name}']:
        instruction = instruction.replace(placeholder, '')
    
    # Vytvoř entity list s VÍCE entitami (aby bylo nejasné)
    entity_list = {}
    domain_entities = all_entities[domain].copy()
    random.shuffle(domain_entities)
    
    # Potřebujeme alespoň 2 entity pro clarify
    num_entities = random.randint(2, min(5, len(domain_entities)))
    entity_list[domain] = domain_entities[:num_entities]
    
    # Přidej další domény
    other_domains = [d for d in all_entities.keys() if d != domain]
    for other_domain in random.sample(other_domains, min(2, len(other_domains))):
        other_entities = all_entities[other_domain].copy()
        random.shuffle(other_entities)
        entity_list[other_domain] = other_entities[:random.randint(2, 4)]
    
    return {
        'instruction': instruction.strip(),
        'entities': entity_list,
        'output': {
            'action': 'clarify',
            'matches': entity_list[domain][:min(3, len(entity_list[domain]))]
        }
    }


def generate_error_sample(
    domain: str,
    service: str,
    phrases: Dict,
    all_entities: Dict[str, List[str]]
) -> Optional[Dict]:
    """
    Generuje ERROR sample (entita nenalezena)
    """
    service_phrases = phrases.get(domain, {}).get(service, {})
    if not service_phrases:
        return None
    
    # Vyber frázi S location
    location_categories = [k for k in service_phrases.keys() if 'with_location' in k]
    
    if not location_categories:
        return None
    
    phrase_category = random.choice(location_categories)
    phrase_template = random.choice(service_phrases[phrase_category])
    
    # Použij NEEXISTUJÍCÍ lokaci pro danou doménu
    fake_locations = {
        'climate': ['ve sklepě', 'na půdě', 'v garáži'],  # climate není v těchto místech
        'cover': ['v koupelně', 'na chodbě', 'v garáži'],  # cover není v těchto místech
        'default': ['ve sklepě', 'na půdě', 'v komůrce']
    }
    
    fake_loc = random.choice(fake_locations.get(domain, fake_locations['default']))
    instruction = phrase_template.replace('{location}', fake_loc)
    
    # Odeber ostatní placeholdery
    for placeholder in ['{brightness}', '{temperature}', '{position}', 
                       '{percentage}', '{value}', '{switch_type}', 
                       '{boolean_name}', '{number_name}', '{name}']:
        instruction = instruction.replace(placeholder, '')
    
    # Vytvoř entity list BEZ matching entity
    entity_list = create_entity_list(all_entities, domain, all_entities[domain][0])
    
    return {
        'instruction': instruction.strip(),
        'entities': entity_list,
        'output': {
            'action': 'error',
            'message': 'Entita nenalezena'
        }
    }


def generate_dataset(services: Dict, phrases: Dict, all_entities: Dict, total_samples: int = 50000) -> List[Dict]:
    """
    Hlavní funkce pro generování celého datasetu
    """
    dataset = []
    
    # Proporce typů vzorků
    execute_count = int(total_samples * 0.60)
    clarify_count = int(total_samples * 0.15)
    error_count = int(total_samples * 0.05)
    getstate_count = total_samples - execute_count - clarify_count - error_count
    
    print(f"\n📊 Generuji vzorky:")
    print(f"   Execute: {execute_count}")
    print(f"   Get State: {getstate_count}")
    print(f"   Clarify: {clarify_count}")
    print(f"   Error: {error_count}")
    print()
    
    # Generuj EXECUTE vzorky
    print("⏳ Generuji Execute samples...")
    attempts = 0
    max_attempts = execute_count * 3  # Max 3x víc pokusů
    
    while len([s for s in dataset if s['output']['action'] == 'execute_service']) < execute_count and attempts < max_attempts:
        domain = random.choice(list(services.keys()))
        service = random.choice(list(services[domain].keys()))
        
        service_config = services[domain][service]
        combo = random.choice(service_config['parameter_combinations'])
        
        sample = generate_execute_sample(domain, service, combo, phrases, all_entities, services)
        
        if sample:
            dataset.append(sample)
            
            if len([s for s in dataset if s['output']['action'] == 'execute_service']) % 1000 == 0:
                print(f"   ✅ {len([s for s in dataset if s['output']['action'] == 'execute_service'])}/{execute_count}")
        
        attempts += 1
    
    # Generuj CLARIFY vzorky
    print("⏳ Generuji Clarify samples...")
    attempts = 0
    max_attempts = clarify_count * 3
    
    while len([s for s in dataset if s['output']['action'] == 'clarify']) < clarify_count and attempts < max_attempts:
        domain = random.choice(list(services.keys()))
        service = random.choice(list(services[domain].keys()))
        
        sample = generate_clarify_sample(domain, service, phrases, all_entities)
        
        if sample:
            dataset.append(sample)
            
            if len([s for s in dataset if s['output']['action'] == 'clarify']) % 1000 == 0:
                print(f"   ✅ {len([s for s in dataset if s['output']['action'] == 'clarify'])}/{clarify_count}")
        
        attempts += 1
    
    # Generuj ERROR vzorky
    print("⏳ Generuji Error samples...")
    attempts = 0
    max_attempts = error_count * 3
    
    while len([s for s in dataset if s['output']['action'] == 'error']) < error_count and attempts < max_attempts:
        domain = random.choice(list(services.keys()))
        service = random.choice(list(services[domain].keys()))
        
        sample = generate_error_sample(domain, service, phrases, all_entities)
        
        if sample:
            dataset.append(sample)
            
            if len([s for s in dataset if s['output']['action'] == 'error']) % 1000 == 0:
                print(f"   ✅ {len([s for s in dataset if s['output']['action'] == 'error'])}/{error_count}")
        
        attempts += 1
    
    # Get State samples (prozatím další execute)
    print("⏳ Get State samples - generuji execute jako placeholder...")
    attempts = 0
    max_attempts = getstate_count * 3
    
    while len(dataset) < total_samples and attempts < max_attempts:
        domain = random.choice(list(services.keys()))
        service = random.choice(list(services[domain].keys()))
        
        service_config = services[domain][service]
        combo = random.choice(service_config['parameter_combinations'])
        
        sample = generate_execute_sample(domain, service, combo, phrases, all_entities, services)
        
        if sample:
            dataset.append(sample)
        
        attempts += 1
    
    # Zamíchej dataset
    random.shuffle(dataset)
    
    return dataset


def main():
    """Hlavní funkce generátoru"""
    print("🚀 HA Voice Training Dataset Generator")
    print("=" * 50)
    
    # Načteme konfigurace
    print("📁 Načítám ha-services.json...")
    services = load_json('ha-services.json')
    
    print("📁 Načítám phrases.json...")
    phrases = load_json('phrases.json')
    
    # Vygenerujeme entity pool
    print("🏠 Generuji entity pool...")
    entities = generate_entity_pool()
    
    print(f"   ✅ Světla: {len(entities['light'])}")
    print(f"   ✅ Topení: {len(entities['climate'])}")
    print(f"   ✅ Žaluzie: {len(entities['cover'])}")
    print(f"   ✅ Spínače: {len(entities['switch'])}")
    print(f"   ✅ Ventilátory: {len(entities['fan'])}")
    print(f"   ✅ Input Boolean: {len(entities['input_boolean'])}")
    print(f"   ✅ Input Number: {len(entities['input_number'])}")
    
    # Generuj dataset
    print("\n" + "=" * 50)
    
    # Pro testování použij 100 vzorků
    TOTAL_SAMPLES = 50000  # Změň na 50000 pro finální běh
    
    dataset = generate_dataset(services, phrases, entities, total_samples=TOTAL_SAMPLES)
    
    # Uložení
    output_path = 'datasets/ha_training_cs.jsonl'
    print(f"\n💾 Ukládám do {output_path}...")
    save_jsonl(dataset, output_path)
    
    print(f"\n✅ Hotovo! Vygenerováno {len(dataset)} vzorků")
    print(f"📁 Soubor: {output_path}")
    
    # Statistiky
    execute_count = len([s for s in dataset if s['output']['action'] == 'execute_service'])
    clarify_count = len([s for s in dataset if s['output']['action'] == 'clarify'])
    error_count = len([s for s in dataset if s['output']['action'] == 'error'])
    
    print(f"\n📊 Statistiky:")
    print(f"   Execute: {execute_count} ({execute_count/len(dataset)*100:.1f}%)")
    print(f"   Clarify: {clarify_count} ({clarify_count/len(dataset)*100:.1f}%)")
    print(f"   Error: {error_count} ({error_count/len(dataset)*100:.1f}%)")


if __name__ == '__main__':
    main()