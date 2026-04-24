#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pdfplumber
import csv
import re
import os
import sys


class ExtractorOP:
    def __init__(self, arquivo_pdf):
        self.arquivo_pdf = arquivo_pdf
        self.dados = []

    def extrair(self):
        if not os.path.exists(self.arquivo_pdf):
            print(f"❌ Erro: Arquivo '{self.arquivo_pdf}' não encontrado.")
            return False

        print(f"📄 Lendo: {self.arquivo_pdf}...\n")
        print("-" * 90)

        try:
            with pdfplumber.open(self.arquivo_pdf) as pdf:
                print(f"Total de páginas: {len(pdf.pages)}\n")

                for i, pagina in enumerate(pdf.pages):
                    texto = pagina.extract_text()

                    if not texto or "ORDEM DE PAGAMENTO" not in texto:
                        continue

                    # ============================
                    # NÚMERO OP
                    # ============================
                    match_op = re.search(
                        r"ORDEM DE PAGAMENTO.*?N[ºo]\s*([\d]+)\s*/\s*(\d+)",
                        texto,
                        re.IGNORECASE | re.DOTALL
                    )
                    numero_op = f"{match_op.group(1)}/{match_op.group(2)}" if match_op else "NÃO ENCONTRADO"

                    # ============================
                    # VALOR TOTAL
                    # ============================
                    match_valor = re.search(r"TOTAL\s+([\d.,]+)", texto)
                    valor_total = match_valor.group(1).strip() if match_valor else "NÃO ENCONTRADO"

                    # ============================
                    # BENEFICIÁRIO
                    # ============================
                    match_beneficiario = re.search(
                        r"INTERESSADO\s+C\.N\.P\.J.*?\n\s*(\d+\s*-\s*[^\n]+)",
                        texto,
                        re.IGNORECASE
                    )
                    beneficiario = match_beneficiario.group(1).strip() if match_beneficiario else "NÃO ENCONTRADO"

                    # ============================
                    # DESTINAÇÃO DE RECURSOS
                    # ============================
                    match_destinacao = re.search(
                        r"(\d{2}\.\d{3}\.\d{4}\s*-\s*[A-ZÇÃÉÍÓÚÂÊÔÜ\s\-]+?)(?:\s+NÃO|\s+SIM|$)",
                        texto
                    )
                    destinacao = match_destinacao.group(1).strip() if match_destinacao else "NÃO ENCONTRADO"

                    # ============================
                    # IRRF
                    # ============================
                    match_ir = re.search(
                        r"IRRF.*?(-?\d{1,3}(?:\.\d{3})*,\d{2})",
                        texto,
                        re.IGNORECASE | re.DOTALL
                    )
                    irrf = match_ir.group(1) if match_ir else "0,00"

                    # ============================
                    # REGISTRO
                    # ============================
                    registro = {
                        "Numero_op": numero_op,
                        "Beneficiario": beneficiario,
                        "Valor_total": valor_total,
                        "IRRF": irrf,
                        "Destinacao_recurso": destinacao,
                        "Pagina": i + 1
                    }

                    self.dados.append(registro)

                    print(f"Pág {i+1:2d} ✓ | OP: {numero_op:8s} | "
                          f"R$ {valor_total:15s} | IR: {irrf:10s}")

            print("-" * 90)
            return True

        except Exception as e:
            print(f"❌ Erro ao ler PDF: {e}")
            return False

    def salvar_csv(self, arquivo_saida):
        if not self.dados:
            print("❌ Erro: Nenhuma informação foi extraída.")
            return False

        try:
            with open(arquivo_saida, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=';')

                # ============================
                # CABEÇALHO
                # ============================
                writer.writerow([
                    "Numero_op",
                    "Beneficiario",
                    "Valor_total",
                    "IRRF",
                    "Destinacao_recurso",
                    "Pagina"
                ])

                # ============================
                # DADOS
                # ============================
                for d in self.dados:
                    writer.writerow([
                        d["Numero_op"],
                        d["Beneficiario"],
                        d["Valor_total"],
                        d["IRRF"],
                        d["Destinacao_recurso"],
                        d["Pagina"]
                    ])

                # ============================
                # RESUMO
                # ============================
                valores = [
                    float(d['Valor_total'].replace('.', '').replace(',', '.'))
                    for d in self.dados if d['Valor_total'] != "NÃO ENCONTRADO"
                ]

                valores_ir = [
                    float(d['IRRF'].replace('.', '').replace(',', '.'))
                    for d in self.dados if d['IRRF'] != "0,00"
                ]

                total_ops = len(self.dados)
                maior = max(valores) if valores else 0
                menor = min(valores) if valores else 0
                soma = sum(valores) if valores else 0
                soma_ir = sum(valores_ir) if valores_ir else 0
                beneficiarios_unicos = len(set(d['Beneficiario'] for d in self.dados))

                writer.writerow([])
                writer.writerow(["RESUMO"])
                writer.writerow(["Total de OPs", total_ops])
                writer.writerow(["Maior valor", f"{maior:.2f}".replace('.', ',')])
                writer.writerow(["Menor valor", f"{menor:.2f}".replace('.', ',')])
                writer.writerow(["Soma total", f"{soma:.2f}".replace('.', ',')])
                writer.writerow(["Total IRRF", f"{soma_ir:.2f}".replace('.', ',')])
                writer.writerow(["Beneficiários únicos", beneficiarios_unicos])

            print(f"\n✅ CSV com resumo gerado: {arquivo_saida}")
            return True

        except Exception as e:
            print(f"❌ Erro ao salvar CSV: {e}")
            return False

    def exibir_resumo(self):
        if not self.dados:
            print("Nenhum dado para exibir.")
            return

        print("\n📊 RESUMO DOS DADOS:")
        print(f"  • Total de OPs: {len(self.dados)}")

        valores = [
            float(d['Valor_total'].replace('.', '').replace(',', '.'))
            for d in self.dados if d['Valor_total'] != "NÃO ENCONTRADO"
        ]

        valores_ir = [
            float(d['IRRF'].replace('.', '').replace(',', '.'))
            for d in self.dados if d['IRRF'] != "0,00"
        ]

        if valores:
            print(f"  • Maior valor: R$ {max(valores):,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'))
            print(f"  • Menor valor: R$ {min(valores):,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'))
            print(f"  • Soma total: R$ {sum(valores):,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'))

        print(f"  • Total IRRF: R$ {sum(valores_ir):,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'))

        beneficiarios = set(d['Beneficiario'] for d in self.dados)
        print(f"  • Beneficiários únicos: {len(beneficiarios)}\n")


def main():
    print("\n" + "="*90)
    print("  EXTRATOR DE ORDENS DE PAGAMENTO - PREFEITURA DE BARUERI")
    print("="*90 + "\n")

    arquivo_entrada = sys.argv[1] if len(sys.argv) > 1 else "OP_CONFERENCIA.pdf"
    arquivo_saida = sys.argv[2] if len(sys.argv) > 2 else "ordens_pagamento.csv"

    extractor = ExtractorOP(arquivo_entrada)

    if extractor.extrair():
        extractor.exibir_resumo()
        extractor.salvar_csv(arquivo_saida)
    else:
        print("❌ Falha na extração do PDF")
        sys.exit(1)


if __name__ == "__main__":
    main()