# Trabalho-PPC

Trabalho de ppc 2021/01

Nosso bar resolveu liberar n rodadas grátis(número aleatório entre 2 e 6) para x clientes presentes no
estabelecimento (número aleatório entre 1 e 5). O bar possui t garçons(número aleatório entre 2 e 7). Cada
garçom consegue atender a z clientes por vez (número aleatório entre 1 e 5). Como essas rodadas são liberadas,
cada garçom somente vai para a copa para buscar o pedido quando todos os 3 clientes que ele pode atender
tiverem feito o pedido ou não houver mais clientes a serem atendidos. Após ter seu pedido atendido, um
cliente pode fazer um novo pedido após consumir sua bebida (o que leva um tempo aleatório) e a definição de
uma nova rodada liberada. Uma nova rodada somente pode ocorrer quando foram atendidos todos os clientes que
fizeram pedidos, além disso todas bebidas devem ser entregues e os clientes por sua vez devem bebe-las. Por
definição, nem todos os clientes precisam pedir uma bebida a cada rodada. Cada cliente tem 50% de chance de
beber ou não. Cada garçom é uma thread, assim como cada cliente é uma thread.
Primeiramente o cliente realiza o pedido ao garçom, que por sua vez anotará o pedido, e logo em seguida levará
ao bartender (o tempo em que o garçom entrega o pedido para o bartender é gerado de forma aleatória). Nem
todos clientes irão beber(devido ao fato que cada cliente tem 50% de chance de beber), e consequentemente não
realizarão pedidos, sendo assim deverão aguardar a próxima rodada. Assim que os pedidos ficarem prontos, os
garçons entregam os pedidos para os clientes atendidos pelos mesmos (existe um tempo aleatório para receberem
os pedidos), e aguardam os clientes terminarem de consumir seu pedido (existe um tempo aleatório para os
clientes terminarem de consumir o pedido), para assim dar início a próxima rodada.
