# --- Predefined mortality rates for Hungarian regions ---
mortality_rates = {
    "BUDAPEST": 0.084847,
    "DÉL-ALFÖLD": 0.123732,
    "DÉL-DUNÁNTÚL": 0.104159,
    "KÖZÉP-DUNÁNTÚL": 0.100511,
    "KÖZÉP-MAGYARORSZÁG": 0.094100,
    "NYUGAT-DUNÁNTÚL": 0.097708,
    "ÉSZAK-ALFÖLD": 0.071052,
    "ÉSZAK-MAGYARORSZÁG": 0.075507
}

# --- Mapping of region capitals/counties to their main region ---
region_capital_mapping = {
    # Budapest and surroundings
    "Budapest": "BUDAPEST",
    "Érd": "BUDAPEST",
    
    # KÖZÉP-MAGYARORSZÁG (Central Hungary) - Pest county
    "Pest": "KÖZÉP-MAGYARORSZÁG",
    "Dunaújváros": "KÖZÉP-MAGYARORSZÁG",
    
    # DÉL-ALFÖLD (Southern Great Plain) - Békés, Csongrád, Bács-Kiskun
    "Békéscsaba": "DÉL-ALFÖLD",
    "Békés": "DÉL-ALFÖLD",
    "Szeged": "DÉL-ALFÖLD",
    "Csongrád": "DÉL-ALFÖLD",
    "Csongrád-Csanád": "DÉL-ALFÖLD",
    "Hódmezôvásárhely": "DÉL-ALFÖLD",
    "Kecskemét": "DÉL-ALFÖLD",
    "Bács-Kiskun": "DÉL-ALFÖLD",
    
    # ÉSZAK-ALFÖLD (Northern Great Plain) - Hajdú-Bihar, Szabolcs, Jász-Nagykun-Szolnok
    "Debrecen": "ÉSZAK-ALFÖLD",
    "Hajdú-Bihar": "ÉSZAK-ALFÖLD",
    "Nyíregyháza": "ÉSZAK-ALFÖLD",
    "Szabolcs-Szatmár-Bereg": "ÉSZAK-ALFÖLD",
    "Szolnok": "ÉSZAK-ALFÖLD",
    "Jász-Nagykun-Szolnok": "ÉSZAK-ALFÖLD",
    
    # DÉL-DUNÁNTÚL (Southern Transdanubia) - Baranya, Somogy, Tolna
    "Pécs": "DÉL-DUNÁNTÚL",
    "Baranya": "DÉL-DUNÁNTÚL",
    "Kaposvár": "DÉL-DUNÁNTÚL",
    "Somogy": "DÉL-DUNÁNTÚL",
    "Szekszárd": "DÉL-DUNÁNTÚL",
    "Tolna": "DÉL-DUNÁNTÚL",
    
    # KÖZÉP-DUNÁNTÚL (Central Transdanubia) - Fejér, Komárom-Esztergom, Veszprém
    "Székesfehérvár": "KÖZÉP-DUNÁNTÚL",
    "Fejér": "KÖZÉP-DUNÁNTÚL",
    "Tatabánya": "KÖZÉP-DUNÁNTÚL",
    "Komárom-Esztergom": "KÖZÉP-DUNÁNTÚL",
    "Veszprém": "KÖZÉP-DUNÁNTÚL",
    
    # NYUGAT-DUNÁNTÚL (Western Transdanubia) - Győr-Moson-Sopron, Vas, Zala
    "Gyôr": "NYUGAT-DUNÁNTÚL",
    "Gyor-Moson-Sopron": "NYUGAT-DUNÁNTÚL",
    "Sopron": "NYUGAT-DUNÁNTÚL",
    "Szombathely": "NYUGAT-DUNÁNTÚL",
    "Vas": "NYUGAT-DUNÁNTÚL",
    "Zalaegerszeg": "NYUGAT-DUNÁNTÚL",
    "Zala": "NYUGAT-DUNÁNTÚL",
    "Nagykanizsa": "NYUGAT-DUNÁNTÚL",
    
    # ÉSZAK-MAGYARORSZÁG (Northern Hungary) - Borsod-Abaúj-Zemplén, Heves, Nógrád
    "Miskolc": "ÉSZAK-MAGYARORSZÁG",
    "Borsod-Abaúj-Zemplén": "ÉSZAK-MAGYARORSZÁG",
    "Eger": "ÉSZAK-MAGYARORSZÁG",
    "Heves": "ÉSZAK-MAGYARORSZÁG",
    "Salgótarján": "ÉSZAK-MAGYARORSZÁG",
    "Nógrád": "ÉSZAK-MAGYARORSZÁG"
}


def get_mortality_rate_for_county(county_name: str):

    # First, check if it's a direct region match (uppercase)
    if county_name in mortality_rates:
        return {float(mortality_rates[county_name])[0]}
    
    # Otherwise, try to find it in the mapping
    if county_name in region_capital_mapping:
        region = region_capital_mapping[county_name]
        return {float(mortality_rates.get(region)[0])}
    
    # If not found, return error
    return {"error": f"Unknown county/region: {county_name}"}
