
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import calendar

app = Flask(__name__)
app.secret_key = "financas_secreto_2024"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///financas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ── MODELS ───────────────────────────────────────────────────────────────────
class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    contas = db.relationship("Conta", backref="grupo", lazy=True)

class Conta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"), nullable=False)
    saidas = db.relationship("Saida", backref="conta", lazy=True)

class Entrada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    origem = db.Column(db.String(200), nullable=False)
    obs = db.Column(db.String(300))

class Saida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    conta_id = db.Column(db.Integer, db.ForeignKey("conta.id"), nullable=False)
    obs = db.Column(db.String(300))

# ── ROUTES ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return redirect(url_for("dashboard"))

# Dashboard
@app.route("/dashboard")
def dashboard():
    hoje = date.today()
    mes = int(request.args.get("mes", hoje.month))
    ano = int(request.args.get("ano", hoje.year))
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])

    entradas = Entrada.query.filter(Entrada.data >= primeiro_dia, Entrada.data <= ultimo_dia).all()
    saidas = Saida.query.filter(Saida.data >= primeiro_dia, Saida.data <= ultimo_dia).all()

    total_entradas = sum(e.valor for e in entradas)
    total_saidas = sum(s.valor for s in saidas)
    saldo = total_entradas - total_saidas

    # Gastos por grupo
    gastos_grupo = {}
    for s in saidas:
        nome_grupo = s.conta.grupo.nome
        gastos_grupo[nome_grupo] = gastos_grupo.get(nome_grupo, 0) + s.valor
    gastos_grupo_sorted = sorted(gastos_grupo.items(), key=lambda x: x[1], reverse=True)

    # Grupo mais caro (%)
    grupo_mais_caro = gastos_grupo_sorted[0] if gastos_grupo_sorted else None
    pct_mais_caro = round((grupo_mais_caro[1] / total_saidas * 100), 1) if grupo_mais_caro and total_saidas > 0 else 0

    meses_nomes = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                   "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

    return render_template("dashboard.html",
        total_entradas=total_entradas, total_saidas=total_saidas, saldo=saldo,
        gastos_grupo=gastos_grupo_sorted, grupo_mais_caro=grupo_mais_caro,
        pct_mais_caro=pct_mais_caro, mes=mes, ano=ano,
        meses_nomes=meses_nomes, total_saidas_ref=total_saidas)

# Grupos
@app.route("/grupos")
def grupos():
    grupos = Grupo.query.order_by(Grupo.nome).all()
    return render_template("grupos.html", grupos=grupos)

@app.route("/grupos/novo", methods=["GET","POST"])
def novo_grupo():
    if request.method == "POST":
        nome = request.form["nome"].strip()
        if not nome:
            flash("Nome do grupo é obrigatório.", "danger")
        elif Grupo.query.filter_by(nome=nome).first():
            flash("Grupo já existe.", "warning")
        else:
            db.session.add(Grupo(nome=nome))
            db.session.commit()
            flash(f"Grupo '{nome}' criado!", "success")
            return redirect(url_for("grupos"))
    return render_template("form_grupo.html")

@app.route("/grupos/editar/<int:id>", methods=["GET","POST"])
def editar_grupo(id):
    g = Grupo.query.get_or_404(id)
    if request.method == "POST":
        g.nome = request.form["nome"].strip()
        db.session.commit()
        flash("Grupo atualizado!", "success")
        return redirect(url_for("grupos"))
    return render_template("form_grupo.html", grupo=g)

@app.route("/grupos/excluir/<int:id>")
def excluir_grupo(id):
    g = Grupo.query.get_or_404(id)
    db.session.delete(g)
    db.session.commit()
    flash("Grupo excluído.", "info")
    return redirect(url_for("grupos"))

# Contas
@app.route("/contas")
def contas():
    contas = Conta.query.order_by(Conta.codigo).all()
    return render_template("contas.html", contas=contas)

@app.route("/contas/nova", methods=["GET","POST"])
def nova_conta():
    grupos = Grupo.query.order_by(Grupo.nome).all()
    if request.method == "POST":
        codigo = request.form["codigo"].strip()
        descricao = request.form["descricao"].strip()
        grupo_id = request.form["grupo_id"]
        if not codigo or not descricao:
            flash("Código e descrição são obrigatórios.", "danger")
        elif Conta.query.filter_by(codigo=codigo).first():
            flash("Código já cadastrado.", "warning")
        else:
            db.session.add(Conta(codigo=codigo, descricao=descricao, grupo_id=grupo_id))
            db.session.commit()
            flash("Conta cadastrada!", "success")
            return redirect(url_for("contas"))
    return render_template("form_conta.html", grupos=grupos)

@app.route("/contas/editar/<int:id>", methods=["GET","POST"])
def editar_conta(id):
    c = Conta.query.get_or_404(id)
    grupos = Grupo.query.order_by(Grupo.nome).all()
    if request.method == "POST":
        c.codigo = request.form["codigo"].strip()
        c.descricao = request.form["descricao"].strip()
        c.grupo_id = request.form["grupo_id"]
        db.session.commit()
        flash("Conta atualizada!", "success")
        return redirect(url_for("contas"))
    return render_template("form_conta.html", conta=c, grupos=grupos)

@app.route("/contas/excluir/<int:id>")
def excluir_conta(id):
    c = Conta.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash("Conta excluída.", "info")
    return redirect(url_for("contas"))

@app.route("/api/contas")
def api_contas():
    q = request.args.get("q","").lower()
    contas = Conta.query.all()
    result = [{"id": c.id, "text": f"{c.codigo} - {c.descricao} ({c.grupo.nome})"} 
              for c in contas if q in c.descricao.lower() or q in c.codigo.lower()]
    return jsonify(result)

# Entradas
@app.route("/entradas")
def entradas():
    lista = Entrada.query.order_by(Entrada.data.desc()).all()
    return render_template("entradas.html", entradas=lista)

@app.route("/entradas/nova", methods=["GET","POST"])
def nova_entrada():
    if request.method == "POST":
        data_str = request.form["data"]
        valor = float(request.form["valor"].replace(",","."))
        origem = request.form["origem"].strip()
        obs = request.form.get("obs","").strip()
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        db.session.add(Entrada(data=data, valor=valor, origem=origem, obs=obs))
        db.session.commit()
        flash("Entrada registrada!", "success")
        return redirect(url_for("entradas"))
    return render_template("form_entrada.html", hoje=date.today().isoformat())

@app.route("/entradas/excluir/<int:id>")
def excluir_entrada(id):
    e = Entrada.query.get_or_404(id)
    db.session.delete(e)
    db.session.commit()
    flash("Entrada excluída.", "info")
    return redirect(url_for("entradas"))

# Saídas
@app.route("/saidas")
def saidas():
    lista = Saida.query.order_by(Saida.data.desc()).all()
    return render_template("saidas.html", saidas=lista)

@app.route("/saidas/nova", methods=["GET","POST"])
def nova_saida():
    if request.method == "POST":
        data_str = request.form["data"]
        valor = float(request.form["valor"].replace(",","."))
        conta_id = request.form["conta_id"]
        obs = request.form.get("obs","").strip()
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        db.session.add(Saida(data=data, valor=valor, conta_id=conta_id, obs=obs))
        db.session.commit()
        flash("Saída registrada!", "success")
        return redirect(url_for("saidas"))
    return render_template("form_saida.html", hoje=date.today().isoformat())

@app.route("/saidas/excluir/<int:id>")
def excluir_saida(id):
    s = Saida.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash("Saída excluída.", "info")
    return redirect(url_for("saidas"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
