#!/usr/bin/env python3
"""
Automação para clicar em um nome específico no Google Forms de votação.

Uso:
    python3 votar.py "Ana Clara Zaghini"
    python3 votar.py "Natália Bonatti Benner" --submit
    python3 votar.py "Natália Bonatti Benner" --submit --iteracoes 5
"""

import argparse
import random
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfCISDAm_Meo7aUJQuY1gPYuIk8VrXCmdmSJEuP4rh-E73c5A/viewform"


def criar_driver(headless: bool = True):
    """Cria e retorna uma instância do Chrome WebDriver."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,900")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def clicar_no_nome(driver, nome_alvo: str):
    """Localiza a opção pelo nome e clica nela."""
    # Aguarda o carregamento do formulário
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='listitem']")))

    # Dá tempo para o JS renderizar todas as opções
    time.sleep(2)

    nome_lower = nome_alvo.lower()

    # Estratégia 1: input radio com data-value ou aria-label contendo o nome
    seletores = [
        f"//div[@role='listitem']//input[@type='radio' and contains(translate(@data-value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{nome_lower}')]",
        f"//div[@role='listitem']//input[@type='radio' and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{nome_lower}')]",
        f"//div[@role='listitem']//*[@role='radio' and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{nome_lower}')]",
    ]

    elemento = None
    for xpath in seletores:
        elementos = driver.find_elements(By.XPATH, xpath)
        if elementos:
            elemento = elementos[0]
            break

    # Estratégia 2: qualquer elemento de opção cujo texto contenha o nome
    if elemento is None:
        xpath_texto = (
            f"//div[@role='listitem']"
            f"//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{nome_lower}')]"
        )
        elementos = driver.find_elements(By.XPATH, xpath_texto)
        for el in elementos:
            texto = (el.text or "").strip()
            if texto and nome_lower in texto.lower():
                elemento = el
                break

    if elemento is None:
        raise RuntimeError(f"Nome '{nome_alvo}' não encontrado no formulário.")

    # Rola até o elemento e clica
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
    time.sleep(0.5)
    elemento.click()

    print(f"✅ Clicado em: {nome_alvo}")


def enviar_formulario(driver):
    """Clica no botão Enviar do formulário."""
    time.sleep(1)
    try:
        botao_enviar = driver.find_element(
            By.XPATH, "//div[@role='button' and .//span[contains(text(),'Enviar')] ]"
        )
        botao_enviar.click()
        print("📤 Formulário enviado.")
    except NoSuchElementException:
        print("⚠️ Botão 'Enviar' não encontrado. Voto marcado, mas não enviado.")


def clicar_enviar_outra_resposta(driver):
    """Clica no link 'Enviar outra resposta' na tela de confirmação."""
    try:
        wait = WebDriverWait(driver, 10)
        link = wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Enviar outra resposta"))
        )
        link.click()
        print("🔄 Nova resposta iniciada.")
        return True
    except TimeoutException:
        print("⚠️ Link 'Enviar outra resposta' não apareceu.")
        return False


def votar(driver, nome_alvo: str, submit: bool = False):
    """Executa um ciclo completo de votação."""
    clicar_no_nome(driver, nome_alvo)

    if submit:
        enviar_formulario(driver)
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description="Clica em um nome no Google Forms de votação.")
    parser.add_argument("nome", help="Nome da pessoa a ser votada.")
    parser.add_argument(
        "--submit", action="store_true", help="Enviar o formulário após clicar no nome."
    )
    parser.add_argument(
        "--visible", action="store_true", help="Abrir o navegador visível (não headless)."
    )
    parser.add_argument(
        "--iteracoes",
        type=int,
        default=1,
        help="Número de vezes que o voto deve ser repetido. Padrão: 1.",
    )
    args = parser.parse_args()

    if args.iteracoes < 1:
        print("❌ O número de iterações deve ser maior ou igual a 1.", file=sys.stderr)
        sys.exit(1)

    driver = None
    try:
        driver = criar_driver(headless=not args.visible)

        for i in range(args.iteracoes):
            print(f"\n--- Iteração {i + 1} de {args.iteracoes} ---")

            if i == 0:
                driver.get(FORM_URL)
            elif args.submit:
                # Após envio, clica em "Enviar outra resposta" para reiniciar
                if not clicar_enviar_outra_resposta(driver):
                    break
            else:
                # Sem envio, simplesmente recarrega o formulário
                driver.get(FORM_URL)

            # Pausa aleatória para simular comportamento humano
            time.sleep(0.5)

            votar(driver, args.nome, submit=args.submit)

    except TimeoutException:
        print("❌ Tempo excedido ao carregar o formulário.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
