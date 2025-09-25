# utils.py

def validar_idmensagem(id_msg):
    """Valida se IDMENSAGEM é um número inteiro válido."""
    if not str(id_msg).isdigit():
        return False
    return True

def formatar_latlong(lat, long):
    """Formata latitude e longitude com 6 casas decimais."""
    try:
        return f"{float(lat):.6f}", f"{float(long):.6f}"
    except (ValueError, TypeError):
        return "", ""

def exibir_alerta(msg):
    """Exibe alerta em janela Tkinter."""
    from tkinter import messagebox
    messagebox.showwarning("Atenção", msg)

def exibir_erro(msg):
    """Exibe erro em janela Tkinter."""
    from tkinter import messagebox
    messagebox.showerror("Erro", msg)

def exibir_info(msg):
    """Exibe informação em janela Tkinter."""
    from tkinter import messagebox
    messagebox.showinfo("Info", msg)
