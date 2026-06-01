import os
import socket
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import RPi.GPIO as GPIO

# Configuração dos pinos GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Definição dos pinos para as saídas
PIN_PLACA_PARE = 18  # Substitua 18 pelo número do pino que você deseja utilizar
PIN_FAIXA_PEDESTRE = 23  # Substitua 23 pelo número do pino que você deseja utilizar
PIN_VELOCIDADE_20 = 24  # Substitua 24 pelo número do pino que você deseja utilizar

# Configuração dos pinos como saídas
GPIO.setup(PIN_PLACA_PARE, GPIO.OUT)
GPIO.setup(PIN_FAIXA_PEDESTRE, GPIO.OUT)
GPIO.setup(PIN_VELOCIDADE_20, GPIO.OUT)


class RFIDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("USO DE IDENTIFICADORES POR RÁDIO FREQUÊNCIA EM SISTEMAS DE MOBILIDADE AUTÔNOMA: COM FOCO NA SEGURANÇA")

        # Configurações da conexão
        self.ip_servidor = "192.168.1.190"
        self.porta_servidor = 6000

        # Variável para armazenar as etiquetas
        self.etiquetas_lidas = {}

        # Elementos da interface
        self.mensagens_frame = ttk.Frame(root)
        self.mensagens_frame.pack(pady=10)

        self.mensagens_treeview = ttk.Treeview(self.mensagens_frame, columns=("Prioridade", "Mensagem", "Código da Etiqueta", "Imagem"))
        self.mensagens_treeview.heading("#1", text="NÍVEL DE PRIORIDADE")
        self.mensagens_treeview.heading("#2", text="PLACA RELACIONADA")
        self.mensagens_treeview.heading("#3", text="CÓDIGO DA ETIQUETA")
        self.mensagens_treeview.heading("#0", text="IMAGEM")
        self.mensagens_treeview.pack(expand=True, fill="both")

        # Centraliza o texto nas colunas
        self.mensagens_treeview.column("#1", anchor="center")
        self.mensagens_treeview.column("#2", anchor="center")
        self.mensagens_treeview.column("#3", anchor="center")

        # Mapeia códigos de etiquetas para caminhos de imagens
        self.imagens_placas = {
            "07 00 EE 00 63 3D 32 AB": "placa_pare.png",
            "07 00 EE 00 D1 4A D4 A5": "placa_pare.png",
            "07 00 EE 00 70 4E D7 55": "placa_pare.png",
            "07 00 EE 00 3A 26 8F 01": "placa_pare.png",
            "07 00 EE 00 9D D5 6C 26": "placa_pare.png",
            "07 00 EE 00 17 56 43 E1": "placa_pare.png",
            "07 00 EE 00 21 5A 5D C9": "placa_pare.png",
            "07 00 EE 00 7F C9 A8 26": "placa_pare.png",
            "07 00 EE 00 8E 2A ED 96": "faixa_pedestre.png",
            "07 00 EE 00 B3 40 6B 5C": "faixa_pedestre.png",
            "07 00 EE 00 7A 5B 8B EF": "faixa_pedestre.png",
            "07 00 EE 00 C0 0D 26 1F": "faixa_pedestre.png",
            "07 00 EE 00 F5 99 91 05": "faixa_pedestre.png",
            "07 00 EE 00 64 BF 20 41": "faixa_pedestre.png",
            "07 00 EE 00 6C 11 94 C3": "faixa_pedestre.png",
            "07 00 EE 00 8F F3 79 C4": "faixa_pedestre.png",
            "07 00 EE 00 9D 02 5E 84": "velocidade_20.png",
            "07 00 EE 00 4C 7E 56 7B": "velocidade_20.png",
            "07 00 EE 00 A8 05 FB 38": "velocidade_20.png",
            "07 00 EE 00 9F E3 69 41": "velocidade_20.png",
            "07 00 EE 00 3C FD 01 3D": "velocidade_20.png",
            "07 00 EE 00 D2 68 AC 8D": "velocidade_20.png",
            "07 00 EE 00 3A 22 AB 47": "velocidade_20.png",
            "07 00 EE 00 C8 69 C4 F4": "velocidade_20.png",
        }

        # Carrega as imagens correspondentes e redimensiona
        self.carregar_imagens()

        # Inicia a thread para ler etiquetas RFID
        self.thread_rfid = threading.Thread(target=self.ler_etiquetas_rfid)
        self.thread_rfid.start()

    def carregar_imagens(self):
        # Cria um dicionário para armazenar objetos ImageTk
        self.imagens = {}

        # Obtém o diretório do script para construir caminhos completos
        diretorio_script = os.path.dirname(os.path.abspath(__file__))

        # Largura desejada para as imagens (ajuste conforme necessário)
        largura_base = 160

        for codigo, caminho_imagem in self.imagens_placas.items():
            caminho_completo = os.path.join(diretorio_script, "imagens", caminho_imagem)

            try:
                # Verifica a existência do arquivo antes de tentar abrir
                if os.path.exists(caminho_completo):
                    imagem = Image.open(caminho_completo)
                    imagem = imagem.resize((largura_base, largura_base))
                    imagem_tk = ImageTk.PhotoImage(imagem)
                    self.imagens[codigo] = imagem_tk
                else:
                    print(f"Arquivo não encontrado: {caminho_completo}")
            except Exception as e:
                print(f"Erro ao carregar imagem {caminho_imagem}: {e}")

    def identificar_mensagem(self, codigo):
        mensagens = {
            "07 00 EE 00 63 3D 32 AB": "PLACA DE PARE",
            "07 00 EE 00 D1 4A D4 A5": "PLACA DE PARE",
            "07 00 EE 00 70 4E D7 55": "PLACA DE PARE",
            "07 00 EE 00 3A 26 8F 01": "PLACA DE PARE",
            "07 00 EE 00 9D D5 6C 26": "PLACA DE PARE",
            "07 00 EE 00 17 56 43 E1": "PLACA DE PARE",
            "07 00 EE 00 21 5A 5D C9": "PLACA DE PARE",
            "07 00 EE 00 7F C9 A8 26": "PLACA DE PARE",
            "07 00 EE 00 8E 2A ED 96": "FAIXA DE PEDESTRE",
            "07 00 EE 00 B3 40 6B 5C": "FAIXA DE PEDESTRE",
            "07 00 EE 00 7A 5B 8B EF": "FAIXA DE PEDESTRE",
            "07 00 EE 00 C0 0D 26 1F": "FAIXA DE PEDESTRE",
            "07 00 EE 00 F5 99 91 05": "FAIXA DE PEDESTRE",
            "07 00 EE 00 64 BF 20 41": "FAIXA DE PEDESTRE",
            "07 00 EE 00 6C 11 94 C3": "FAIXA DE PEDESTRE",
            "07 00 EE 00 8F F3 79 C4": "FAIXA DE PEDESTRE",
            "07 00 EE 00 9D 02 5E 84": "VELOCIDADE DA VIA 20KM/H",
            "07 00 EE 00 4C 7E 56 7B": "VELOCIDADE DA VIA 20KM/H",
            "07 00 EE 00 A8 05 FB 38": "VELOCIDADE DA VIA 20KM/H",
            "07 00 EE 00 9F E3 69 41": "VELOCIDADE DA VIA 20KM/H",
            "07 00 EE 00 3C FD 01 3D": "VELOCIDADE DA VIA 20KM/H",
            "07 00 EE 00 D2 68 AC 8D": "VELOCIDADE DA VIA 20KM/H",
            "07 00 EE 00 3A 22 AB 47": "VELOCIDADE DA VIA 20KM/H",
            "07 00 EE 00 C8 69 C4 F4": "VELOCIDADE DA VIA 20KM/H",
        }

        return mensagens.get(codigo)

    def obter_prioridade(self, codigo):
        prioridades = {
            "07 00 EE 00 63 3D 32 AB": 1,
            "07 00 EE 00 D1 4A D4 A5": 1,
            "07 00 EE 00 70 4E D7 55": 1,
            "07 00 EE 00 3A 26 8F 01": 1,
            "07 00 EE 00 9D D5 6C 26": 1,
            "07 00 EE 00 17 56 43 E1": 1,
            "07 00 EE 00 21 5A 5D C9": 1,
            "07 00 EE 00 7F C9 A8 26": 1,
            "07 00 EE 00 8E 2A ED 96": 2,
            "07 00 EE 00 B3 40 6B 5C": 2,
            "07 00 EE 00 7A 5B 8B EF": 2,
            "07 00 EE 00 C0 0D 26 1F": 2,
            "07 00 EE 00 F5 99 91 05": 2,
            "07 00 EE 00 64 BF 20 41": 2,
            "07 00 EE 00 6C 11 94 C3": 2,
            "07 00 EE 00 8F F3 79 C4": 2,
            "07 00 EE 00 9D 02 5E 84": 3,
            "07 00 EE 00 4C 7E 56 7B": 3,
            "07 00 EE 00 A8 05 FB 38": 3,
            "07 00 EE 00 9F E3 69 41": 3,
            "07 00 EE 00 3C FD 01 3D": 3,
            "07 00 EE 00 D2 68 AC 8D": 3,
            "07 00 EE 00 3A 22 AB 47": 3,
            "07 00 EE 00 C8 69 C4 F4": 3,
        }

        return prioridades.get(codigo, 0)

    def processar_etiqueta(self, hex_representation):
        # Verifica se a etiqueta já foi lida antes
        if hex_representation not in self.etiquetas_lidas:
            # Adiciona a etiqueta ao dicionário de etiquetas lidas
            prioridade = self.obter_prioridade(hex_representation)
            mensagem = self.identificar_mensagem(hex_representation)

            if mensagem is not None:
                self.adicionar_mensagem_tela(hex_representation, prioridade, mensagem)

            self.etiquetas_lidas[hex_representation] = {
                'prioridade': prioridade,
                'mensagem': mensagem,
                'timestamp': time.time()
            }
        else:
            # Atualiza o timestamp da última leitura para evitar a remoção
            self.etiquetas_lidas[hex_representation]['timestamp'] = time.time()


        # Controla as saídas digitais com base no código da etiqueta RFID
        if hex_representation in self.imagens_placas:
            caminho_imagem = self.imagens_placas[hex_representation]
            if "placa_pare.png" in caminho_imagem:
                GPIO.output(PIN_PLACA_PARE, GPIO.HIGH)
                GPIO.output(PIN_FAIXA_PEDESTRE, GPIO.LOW)
                GPIO.output(PIN_VELOCIDADE_20, GPIO.LOW)
            elif "faixa_pedestre.png" in caminho_imagem:
                GPIO.output(PIN_PLACA_PARE, GPIO.LOW)
                GPIO.output(PIN_FAIXA_PEDESTRE, GPIO.HIGH)
                GPIO.output(PIN_VELOCIDADE_20, GPIO.LOW)
            elif "velocidade_20.png" in caminho_imagem:
                GPIO.output(PIN_PLACA_PARE, GPIO.LOW)
                GPIO.output(PIN_FAIXA_PEDESTRE, GPIO.LOW)
                GPIO.output(PIN_VELOCIDADE_20, GPIO.HIGH)
     

    def adicionar_mensagem_tela(self, etiqueta, prioridade, mensagem):
        # Adiciona uma nova linha à Treeview
        item_id = self.mensagens_treeview.insert("", "end", values=(prioridade, mensagem, etiqueta),
                                                 tags=(f"prioridade_{prioridade}",))

        # Define cores para diferentes prioridades
        cores = ["#FF0000", "#FFFF00", "#00FF00"]  # Vermelho, Amarelo, Verde
        cor_prioridade = cores[prioridade - 1]
        self.mensagens_treeview.tag_configure(f"prioridade_{prioridade}", background=cor_prioridade)


        # Exibe a imagem correspondente à etiqueta (se existir)
        if etiqueta in self.imagens:
            imagem = self.imagens[etiqueta]
            # Verifica se o item ainda existe antes de tentar atualizá-lo
            if self.mensagens_treeview.exists(item_id):
                self.mensagens_treeview.item(item_id, image=imagem)

    def remover_etiquetas_expiradas(self):
        # Remove etiquetas que não foram lidas por mais de 2 segundos
        etiquetas_remover = [etiqueta for etiqueta, info in self.etiquetas_lidas.items()
                             if time.time() - info['timestamp'] > 2]
        for etiqueta_remover in etiquetas_remover:
            self.remover_mensagem_tela(etiqueta_remover)
            del self.etiquetas_lidas[etiqueta_remover]
            

    def remover_mensagem_tela(self, etiqueta):
        # Remove a linha correspondente à etiqueta na Treeview
        for item_id in self.mensagens_treeview.get_children():
            if self.mensagens_treeview.item(item_id, "values")[2] == etiqueta:
                self.mensagens_treeview.delete(item_id)
                break
                # Desliga todas as saídas digitais
        GPIO.output(PIN_PLACA_PARE, GPIO.LOW)
        GPIO.output(PIN_FAIXA_PEDESTRE, GPIO.LOW)
        GPIO.output(PIN_VELOCIDADE_20, GPIO.LOW)

    def ler_etiquetas_rfid(self):
        while True:
            try:
                # Tenta estabelecer a conexão com o servidor RFID
                with socket.create_connection((self.ip_servidor, self.porta_servidor)) as s:
                    while True:
                        # Envia um comando para ler a etiqueta RFID
                        comando_leitura = b"READ_RFID"
                        s.sendall(comando_leitura)

                        # Recebe os dados da etiqueta RFID
                        dados_etiqueta = s.recv(1024)

                        # Converte os dados para representação hexadecimal
                        hex_representation = ' '.join([f'{byte:02X}' for byte in dados_etiqueta])

                        # Verifica se a etiqueta já foi lida antes
                        self.processar_etiqueta(hex_representation)

                        # Remove etiquetas expiradas
                        self.remover_etiquetas_expiradas()

                        # Aguarda 0,5 segundos antes da próxima leitura
                        time.sleep(0.5)

            except socket.error as e:
                self.mostrar_mensagem_desconectado()
                print(f"Erro ao conectar: {e}")
                time.sleep(5)  # Aguarda 5 segundos antes de tentar reconectar

    def mostrar_mensagem_desconectado(self):
        # Mostra mensagem de desconexão e remove todas as mensagens
        messagebox.showwarning("Desconexão", "A antena RFID foi desconectada.")
        self.remover_mensagens_tela()
                # Desliga todas as saídas digitais
        GPIO.output(PIN_PLACA_PARE, GPIO.LOW)
        GPIO.output(PIN_FAIXA_PEDESTRE, GPIO.LOW)
        GPIO.output(PIN_VELOCIDADE_20, GPIO.LOW)

if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDApp(root)
    root.mainloop()
    
    try:
        root = tk.Tk()
        app = RFIDApp(root)
        root.mainloop()
    finally:
        # Desliga todas as saídas digitais antes de sair
        GPIO.output(PIN_PLACA_PARE, GPIO.LOW)
        GPIO.output(PIN_FAIXA_PEDESTRE, GPIO.LOW)
        GPIO.output(PIN_VELOCIDADE_20, GPIO.LOW)
        # Limpa a configuração dos pinos GPIO
        GPIO.cleanup()
