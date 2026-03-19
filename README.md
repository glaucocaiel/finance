# 💰 Finanças Pessoais

App web de gestão financeira pessoal com Flask + SQLite.

## Funcionalidades
- Cadastro de Grupos e Contas
- Lançamentos de Entradas (data, valor, origem)
- Lançamentos de Saídas (data, pesquisa de conta, valor)
- Dashboard com totais, saldo, gastos por grupo e gráfico

## Rodando Localmente
```bash
pip install -r requirements.txt
python app.py
```
Acesse: http://localhost:5000

## Deploy Gratuito no Render.com
1. Suba este repositório no GitHub
2. Acesse https://render.com e crie uma conta
3. Clique em "New Web Service" → conecte o repositório
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`
6. Clique em "Create Web Service"

Pronto! Sua URL estará disponível gratuitamente.
