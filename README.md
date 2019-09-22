# crawler-challenge

Objetivo

Desenvolver um crawler em python para extração de dados dos sites-alvo, arquivar os resultados em banco sqlite e permitir visualização dos dados

Sites alvo
- DigitalOcean (https://www.digitalocean.com/pricing/#droplet)
- Vultr (https://www.vultr.com/pricing/)
- Packet (https://www.packet.com/cloud/servers/)

Extrair os dados de oferta de todas as máquinas cloud nos três sites, com as seguintes informações:
- Nome do serviço/site
- Nome da máquina
- CPUs
- Memória
- Storage
- Quantidade de transfer/bandwidth por mês
- Valor por hora
- Valor por mês

Salvar os dados em uma base sqlite depois de tratados sem que haja duplicação

Permitir através da linha de comando exibir os dados já salvos.

Condições de contorno
- Script em python 3
- Dados salvos em sqlite
- Comandos CLI para: download dos dados, visualização, help

