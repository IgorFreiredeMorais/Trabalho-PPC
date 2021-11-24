#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Igor Freire de Morais 201911142
@author: Nathan Araújo Silva 201910762
"""

import threading
import time
import random
import collections
import logging
import argparse

# Configuraçoes do log
logging.basicConfig(level=logging.DEBUG, format='%(message)s',)


class Cliente(threading.Thread):
    """Classe Cliente do tipo Thread"""
    def __init__(self, nome, gerenciador):
        threading.Thread.__init__(self)
        self.nome = nome
        # gerenciador compartilhado
        self.gerenciador = gerenciador
        # quando der self.e_esperar.wait() a thread espera receber o pedido
        self.e_esperar = threading.Event()
        self.beber = True

    def continuar(self):
        # o garçon utiliza esse metodo para acordar o cliente
        self.e_esperar.set()

    def fazPedido(self):
        """50% de chance do cliente beber"""
        chance = random.randint(0, 1)
        if chance == 1:
            # se nao quiser beber fala para o gerente que nao bebera e
            # o garcom ira o acordar e em seguida esperara a prox. rodada
            self.beber = False
            self.gerenciador.nao_quer_beber(self)
            self.e_esperar.wait()
            # habilita o lock interno do e_esperar para poder dar wait (again)
            self.e_esperar.clear()
            logging.info(" ".join(["Cliente",
                                   str(self.nome),
                                   "não irá beber"]))
            # espera a proxima rodada
            self.gerenciador.espera_beberem()
        else:
            self.beber = True
            # se coloca para ser atendido
            self.gerenciador.pedir(self)

    def esperaPedido(self):
        """Espera o garcom acordar ele e
           depois libera o cliente para poder esperar novamente (.clear())"""
        self.e_esperar.wait()
        self.e_esperar.clear()

    def recebePedido(self):
        """Tempo random para ele pegar o pedido do garcom antes de beber"""
        tempo = random.randint(1, 2)
        time.sleep(tempo)
        logging.info(" ".join(["Cliente",
                     str(self.nome),
                     "está bebendo"]))

    def consomePedido(self):
        """Toma em um tempo aleatório e espera todos tomarem para iniciar a proxima rodada"""
        tempo = random.randint(1, 2)
        time.sleep(tempo)
        logging.info(" ".join(["Cliente",
                     str(self.nome),
                     "terminou de beber"]))
        self.gerenciador.espera_beberem()

    def run(self):
        """Enquanto o bar nao fechar, testa se o cliente beberá se sim, faz o pedido, espera e consome"""
        while not self.gerenciador.fechou():
            self.fazPedido()
            if self.beber:
                self.esperaPedido()
                self.recebePedido()
                self.consomePedido()


class Garcom(threading.Thread):
    """Classe garcom do tipo thread"""
    def __init__(self, max_cli, nome, gerenciador):
        threading.Thread.__init__(self)
        self.nome = nome
        # gerenciador compartilhado
        self.gerenciador = gerenciador
        # maximo de clientes que ele pode atender
        self.max_cli = max_cli
        # lista de clientes que o garcom anotou
        self.anotados = []

    def recebeMaximoPedidos(self):
        """Anota os pedidos dos clientes até alcançar seu maximo de pedidos ou nao ter mais clientes para atender na rodada"""
        while len(self.anotados) < self.max_cli:
            cliente_atual = self.gerenciador.anotar_pedido(self)
            # verifica se ainda tem clientes para serem atendidos na rodada
            # if cliente_atual != -1:
            if cliente_atual is not None:
                if cliente_atual.beber:
                    self.anotados.append(cliente_atual)
                    logging.info(" ".join(["Garçom",
                                 str(self.nome),
                                 "anotou o pedido do cliente",
                                 str(cliente_atual.nome)]))
                else:
                    # se o cliente nao quiser beber deixa ele esperar prox. rod
                    cliente_atual.continuar()
            else:
                # nao existem mais clientes para serem atendidos na rodada
                break

    def registraPedidos(self):
        """Leva os pedidos para o balcao, se o garcom tiver anotado algum pedido"""
        if len(self.anotados) > 0:
            # randomiza um tempo que ele leva para ir ate a copa
            tempo = random.randint(1, 2)
            time.sleep(tempo)
            logging.info(" ".join(["Garçom",
                         str(self.nome),
                         "levou para o bartender os pedidos dos clientes",
                         str([i.nome for i in self.anotados])]))

    def entregaPedidos(self):
        """Vai de cliente em cliente da lista e entrega o pedido do garcom"""
        for i in self.anotados:
            # acorda a thread do cliente para ele poder receber e beber
            i.continuar()  # e_esperar.set()
            logging.info(" ".join(["Garçom",
                         str(self.nome),
                         "entregou para o Cliente",
                         str(i.nome)]))

        # limpa a lista de pedidos do garcom
        self.anotados.clear()

    def run(self):
        """Enquanto o bar nao fechar o garcom pega o maximo de pedidos que conseguir e os entrega"""
        while not self.gerenciador.fechou():
            self.recebeMaximoPedidos()
            self.registraPedidos()
            self.entregaPedidos()


class Gerenciador():
    """Permite exclusao mutua entre as threads e bloqueia açoes ate certas condicoes serem satisfeitas"""
    def __init__(self, numClientes, totalRodada):
        # lugar do cliente que quer beber e do que nao quer no prod. consumidor
        self.buff_quer = collections.deque([], 1)
        self.buff_naoQuer = collections.deque([], 1)
        # lock que impede que garcons e cluentes acessem as listas acima juntos
        self.lock = threading.Condition()
        # clientes podem entrar na area critica
        self.vazio = threading.Semaphore(1)
        # garcons podem entrar na area critica
        self.cheio = threading.Semaphore(0)

        # numero de clientes que o bar possui
        self.numClientes = numClientes
        # quantidade de rodadas que ocorrerao
        self.totalRodada = totalRodada

        # total de pedidos entregues na rodada
        self.totalEntregue = 0
        # total de pedidos anotados e de clientes que nao querem beber na rod.
        self.totalAnotado = 0
        # numero da rodada atual
        self.rodada = 0
        # numero de clientes que precisam terminar de beber para a prox. rod.
        self.faltaBeber = numClientes

        # condicoes que permitem exclusao mutua
        self.lockEsperaTodosBeberem = threading.Condition()
        self.fechaAnotacao = threading.Condition()

    def espera_beberem(self):
        """Espera todos beberem para comecar a nova rodada"""
        with self.lockEsperaTodosBeberem:
            # um cliente entra aqui por vez se ele for o ultimo libera todos
            if self.faltaBeber - 1 == 0:
                # reinicia o numero de pessoas que faltam beber
                self.faltaBeber = self.numClientes
                self.rodada += 1
                # zera o numero de total de anotados para iniciar a prox rodada
                """self.muda_totalAnotado(False)"""

                if self.rodada == self.totalRodada:
                    logging.info("\nACABARAM AS RODADAS GRÁTIS!!!")
                else:
                    self.totalAnotado = 0
                    
                    if self.rodada == 0 :
                      numRodada = "Primeira"
                    elif self.rodada == 1 :
                      numRodada = "Segunda"
                    elif self.rodada == 2 :
                      numRodada = "Terceira"
                    elif self.rodada == 3 :
                      numRodada = "Quarta"
                    elif self.rodada == 4 :
                      numRodada = "Quinta"
                    else:
                      numRodada = "Sexta"

                    logging.info(" ".join([str(numRodada),"rodada"]))
                # libera todos os clientes para voltarem a pedir
                self.lockEsperaTodosBeberem.notifyAll()
            else:
                self.faltaBeber -= 1
                # trava o cliente que esta nessa area ate o ultimo destravar
                # todos os que estiverem aqui (o wait libera o lock)
                self.lockEsperaTodosBeberem.wait()

    def fechou(self):
        """O bar fecha quando a rodada atual for igual o maximo de rodadas"""
        return self.totalRodada == self.rodada

    def pedir(self, cliente):
        """Adiciona o cliente (que bebera) para ser atendido"""
        self.vazio.acquire()
        with self.lock:
            self.buff_quer.append(cliente)
        self.cheio.release()

    def nao_quer_beber(self, cliente):
        """Adiciona o cliente (que nao bebera) para ser atendido"""
        self.vazio.acquire()
        with self.lock:
            self.buff_naoQuer.append(cliente)
        # libera lara um garcom retira-lo
        self.cheio.release()

    def anotar_pedido(self, garcom):
        """Consome o primeiro cliente que pedir (estiver no produtor consu.)"""
        with self.fechaAnotacao:
            # verifica se todos ja foram atendidos
            if self.totalAnotado < self.numClientes:
                self.cheio.acquire()
                with self.lock:
                    # verifica se o cliente adicionado bebera ou nao
                    if len(self.buff_quer) == 1:
                        cliente_atendido = self.buff_quer.popleft()
                    else:
                        cliente_atendido = self.buff_naoQuer.popleft()

                    # libera para um novo cliente ser adicionado
                    self.vazio.release()
                    self.totalAnotado += 1
                    # retorna o cliente que foi atendido
                    return cliente_atendido
            else:
                # retornando None o garcom sabera que todos da rod. foram atend
                return None

def parse_argumentos():
    """Faz o parse dos argumentos"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--numClientes', help='Numero de Clientes. [5]', type=int, default=5)
    parser.add_argument('--numGarcons', help='Numero de garcons. [3]', type=int, default=3)
    parser.add_argument('--capacidadeGarcons', help='Capacidade dos garcons. [3]', type=int, default=3)
    parser.add_argument('--numRodadas', help='Numero de rodadas. [6]', type=int, default=6)
    return parser.parse_args()

def main():
    # faz o parse dos argumentos recebidos
    args = parse_argumentos()

    logging.info(" ".join(["\nNossos",
                           str(args.numGarcons),"garçons irão distribuir",
                           str(args.numRodadas),"rodadas grátis para voces",
                           str(args.numClientes),"clientes, mas eles somente pegarao",
                           str(args.capacidadeGarcons),"pedidos por vez"]))
    logging.info("\nVAMOS INICIAR A PRIMEIRA RODADA!!!")

    # verifica se o bar possui clientes
    if args.numClientes > 0:
        # Cria o objeto gerente que sera passado aos garcons e clientes
        gerente = Gerenciador(args.numClientes, args.numRodadas)

        # Cria numGarcons garcons atribuindo i como o nome deles
        garcons = [Garcom(args.capacidadeGarcons, i, gerente) for i in range(args.numGarcons)]

        # Cria numClientes Clientes atribuindo i como o nome deles
        clientes = [Cliente(i, gerente) for i in range(args.numClientes)]

        # inicia os garcons e clientes
        for i in garcons:
            i.start()
        for i in clientes:
            i.start()
        for i in clientes:
            i.join()
        logging.info("\nClientes foram embora.")
        for i in garcons:
            i.join()
    logging.info("\nGarçons pararam de servir.")

if __name__ == '__main__':
    main()
