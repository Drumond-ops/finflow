from datetime import datetime
from fpdf import FPDF


def formatar_moeda(centavos) -> str:
    """Converte centavos em string formatada em Reais: R$ 1.250,50"""
    valor_reais = float(centavos or 0) / 100.0
    return f"R$ {valor_reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

class FinFlowPDF(FPDF):
    def header(self):
        # Título do Relatório
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 41, 59) # Azul ardósia escuro
        self.cell(0, 10, "FinFlow - Relatório Financeiro Mensal", align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
    def footer(self):
        # Rodapé com número da página
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

def gerar_pdf_mensal(usuario, mes: int, ano: int, transacoes_correntes, faturas_detalhadas) -> bytes:
    pdf = FinFlowPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    # 1. Informações do Usuário e Período
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, f"Usuário: {usuario.nome} ({usuario.email})", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Período de Referência: {mes:02d}/{ano}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    # 2. SEÇÃO: Extrato de Receitas e Despesas Correntes
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, " 1. Extrato de Transações Correntes (Conta/Débito/Pix)", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    if not transacoes_correntes:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 7, "Nenhuma transação corrente registrada neste mês.", new_x="LMARGIN", new_y="NEXT")
    else:
        # Cabeçalho da Tabela
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(226, 232, 240)
        pdf.cell(25, 7, "Data", border=1, fill=True)
        pdf.cell(75, 7, "Descrição", border=1, fill=True)
        pdf.cell(45, 7, "Categoria", border=1, fill=True)
        pdf.cell(20, 7, "Tipo", border=1, fill=True)
        pdf.cell(25, 7, "Valor", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=9)
        for t in transacoes_correntes:
            data_str = t["data"].strftime("%d/%m/%Y") if hasattr(t["data"], "strftime") else str(t["data"])
            cor_tipo = (22, 101, 52) if t["tipo"] == "receita" else (185, 28, 28)
            
            pdf.set_text_color(15, 23, 42)
            pdf.cell(25, 6, data_str, border=1)
            pdf.cell(75, 6, (t["descricao"] or "Sem descrição")[:40], border=1)
            pdf.cell(45, 6, t["categoria_nome"][:25], border=1)
            
            pdf.set_text_color(*cor_tipo)
            pdf.cell(20, 6, t["tipo"].capitalize(), border=1)
            
            pdf.set_text_color(15, 23, 42)
            pdf.cell(25, 6, formatar_moeda(t["valor"]), border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    # 3. SEÇÃO: Extrato de Faturas por Cartão e Acompanhamento de Planejamento
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, " 2. Extrato de Faturas por Cartão de Crédito", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    if not faturas_detalhadas:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 7, "Nenhum cartão cadastrado ou nenhuma fatura com movimentação.", new_x="LMARGIN", new_y="NEXT")
    else:
        for fatura in faturas_detalhadas:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(0, 7, f"Cartão: {fatura['nome_cartao']} | Total da Fatura: {formatar_moeda(fatura['valor_total'])}", new_x="LMARGIN", new_y="NEXT")
            # Compras da fatura
            if fatura["compras"]:
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_fill_color(248, 250, 252)
                pdf.cell(25, 6, "Data", border=1, fill=True)
                pdf.cell(90, 6, "Descrição", border=1, fill=True)
                pdf.cell(50, 6, "Categoria", border=1, fill=True)
                pdf.cell(25, 6, "Valor", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", size=8)
                for c in fatura["compras"]:
                    d_str = c["data"].strftime("%d/%m/%Y") if hasattr(c["data"], "strftime") else str(c["data"])
                    pdf.cell(25, 5, d_str, border=1)
                    pdf.cell(90, 5, (c["descricao"] or "Compra")[:45], border=1)
                    pdf.cell(50, 5, c["categoria_nome"][:25], border=1)
                    pdf.cell(25, 5, formatar_moeda(c["valor"]), border=1, align="R", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_font("Helvetica", "I", 8)
                pdf.cell(0, 5, "Nenhuma compra registrada neste cartão no período.", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            # Tabela de Planejamento vs Utilizado (RF12)
            if fatura["planejamentos"]:
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 6, "Acompanhamento do Planejamento da Fatura:", new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_fill_color(241, 245, 249)
                pdf.cell(60, 6, "Categoria", border=1, fill=True)
                pdf.cell(40, 6, "Limite Planejado", border=1, fill=True, align="R")
                pdf.cell(40, 6, "Gasto Realizado", border=1, fill=True, align="R")
                pdf.cell(30, 6, "Saldo Restante", border=1, fill=True, align="R")
                pdf.cell(20, 6, "% Utilizado", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", size=8)
                for p in fatura["planejamentos"]:
                    pdf.cell(60, 5, p["nome_categoria"], border=1)
                    pdf.cell(40, 5, formatar_moeda(p["valor_planejado"]), border=1, align="R")
                    pdf.cell(40, 5, formatar_moeda(p["valor_gasto"]), border=1, align="R")
                    pdf.cell(30, 5, formatar_moeda(p["saldo"]), border=1, align="R")
                    pdf.cell(20, 5, f"{p['percentual']}%", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
    return bytes(pdf.output())