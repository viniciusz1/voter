#!/usr/bin/env python3
"""Script de diagnóstico para entender porque o clique não funciona."""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfCISDAm_Meo7aUJQuY1gPYuIk8VrXCmdmSJEuP4rh-E73c5A/viewform"
NOME = "Natália Bonatti Benner"


def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,1200")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print("Abrindo formulário...")
        driver.get(FORM_URL)

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='listitem']")))
        time.sleep(3)

        print("Salvando screenshot inicial...")
        driver.save_screenshot("screenshot_inicial.png")

        print("Salvando HTML...")
        with open("pagina.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        # Lista todos os elementos que contêm o nome
        print(f"\nBuscando elementos com texto '{NOME}':")
        xpath = f"//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{NOME.lower()}')]"
        elementos = driver.find_elements(By.XPATH, xpath)
        print(f"Encontrados {len(elementos)} elementos")

        for i, el in enumerate(elementos[:10]):
            tag = el.tag_name
            texto = (el.text or "").strip()[:80]
            role = el.get_attribute("role")
            classes = el.get_attribute("class")
            print(f"  {i}: <{tag} role={role}> texto='{texto}' classes='{classes[:60] if classes else ''}'")

        # Tenta clicar no primeiro elemento com texto não vazio
        alvo = None
        for el in elementos:
            texto = (el.text or "").strip()
            if texto and NOME.lower() in texto.lower():
                alvo = el
                break

        if alvo:
            print(f"\nTentando clicar em: {alvo.tag_name}")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", alvo)
            time.sleep(1)
            driver.save_screenshot("screenshot_antes_clique.png")
            alvo.click()
            print("Clique realizado.")
            time.sleep(2)
            driver.save_screenshot("screenshot_depois_clique.png")
        else:
            print("Nenhum elemento com texto exato encontrado.")

        # Procura por radio buttons/checkboxes
        print("\nBuscando inputs do tipo radio/checkbox:")
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
        print(f"Encontrados {len(inputs)} inputs")
        for i, inp in enumerate(inputs[:5]):
            print(f"  {i}: type={inp.get_attribute('type')} value={inp.get_attribute('value')[:50]}")

    except Exception as e:
        print(f"Erro: {e}")
        driver.save_screenshot("screenshot_erro.png")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
