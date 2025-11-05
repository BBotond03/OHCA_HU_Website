# --- Predefined mortality rates for Hungarian regions ---# not real mortality rates rn!!!
mortality_rates = {
    "BUDAPEST": 0.092,
    "DÉL-ALFÖLD": 0.11,
    "DÉL-DUNÁNTÚL": 0.095,
    "KÖZÉP-DUNÁNTÚL": 0.10,
    "KÖZÉP-MAGYARORSZÁG": 0.09,
    "NYUGAT-DUNÁNTÚL": 0.092,
    "ÉSZAK-ALFÖLD": 0.06,
    "ÉSZAK-MAGYARORSZÁG": 0.08
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
    if not county_name or not county_name.strip():
        return {"error": "No county/region provided"}

    normalized = county_name.strip()

    # Direct region match (case-insensitive comparison to tolerate different capitalisations)
    for region_name, rate in mortality_rates.items():
        if region_name.upper() == normalized.upper():
            return rate

    # Lookup through capital/county mapping (case-insensitive as well)
    region_key = None
    if normalized in region_capital_mapping:
        region_key = region_capital_mapping[normalized]
    else:
        for key, mapped_region in region_capital_mapping.items():
            if key.upper() == normalized.upper():
                region_key = mapped_region
                break

    if region_key:
        rate = mortality_rates.get(region_key)
        if rate is not None:
            return rate

    # If not found, return error
    return {"error": f"Unknown county/region: {county_name}"}
