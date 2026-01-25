# 📖 Referência Completa de Comandos

Guia detalhado de todos os comandos disponíveis no Bot de Promoções.

## 🎯 Visão Geral

Todos os comandos devem ser enviados no **chat privado** com o bot. Apenas o usuário configurado em `ADMIN_USER_ID` pode executá-los.

---

## 📊 Comandos de Status

### `/status`
Exibe informações sobre o estado atual do bot.

**Uso:**
```
/status
```

**Retorna:**
- Modo de operação atual (Manual/Autônomo)
- Total de ofertas no banco de dados
- Status de conexão

**Exemplo de resposta:**
```
🤖 Bot Online & Operante

📊 Modo: Autônomo
📉 Banco de Dados: 142 itens
✨ Envie um link direto para postar agora!
```

---

## 🤖 Modo de Operação

### `/auto`
Alterna entre Modo Manual e Modo Autônomo.

**Uso:**
```
/auto
```

**Comportamento:**

| Modo | Ofertas Score > 60 | Ofertas Score 40-60 | Ofertas Score < 40 |
|------|-------------------|---------------------|-------------------|
| **Manual** | Admin aprova | Admin aprova | Admin aprova |
| **Autônomo** | 🤖 Posta automaticamente | Admin aprova | Descartadas |

**Exemplo de resposta (ativando):**
```
🤖 Modo AUTÔNOMO Ativado

O bot agora postará automaticamente ofertas com score alto (>60) 
diretamente no canal. Ofertas com score médio (40-60) ainda 
precisarão de sua aprovação.

💡 Use /auto novamente para alternar.
```

**Exemplo de resposta (desativando):**
```
👤 Modo MANUAL Ativado

O bot agora enviará todas as ofertas para você aprovar 
antes de postar no canal.

💡 Use /auto novamente para alternar.
```

---

## 🔍 Comandos de Busca

### `/scan`
Força uma busca imediata no Hub de Afiliados, ignorando o intervalo de 30 minutos.

**Uso:**
```
/scan
```

**Retorna:**
```
🔎 Forçando nova busca...
O bot vai vasculhar as lojas agora mesmo e te avisar se encontrar algo!
```

**Quando usar:**
- Você quer verificar novas ofertas imediatamente
- Acabou de adicionar uma palavra-chave e quer testar
- Quer validar se o bot está funcionando

---

## 🔗 Comandos de Links Manuais

### `/add [link]`
Adiciona um link específico para processamento imediato.

**Uso:**
```
/add https://produto.mercadolivre.com.br/MLB-123456789
```

**Retorna:**
```
✅ Link agendado para processamento!
```

**Alternativa:** Você também pode simplesmente **colar o link** no chat (sem comando):
```
https://produto.mercadolivre.com.br/MLB-123456789
```

**Comportamento:**
1. Bot extrai informações do produto
2. Gera link de afiliado automaticamente
3. Posta **diretamente no canal** (não passa por aprovação)

**Quando usar:**
- Você encontrou uma oferta boa manualmente
- Quer postar algo específico rapidamente
- Está testando um produto

---

## 🔥 Gerenciamento de Palavras-Chave

### `/hot [termo]`
Adiciona uma palavra-chave à lista de busca ativa.

**Uso:**
```
/hot airpods
```

**Retorna:**
```
🔥 'airpods' adicionado à busca ativa!
```

**Nota:** Atualmente o bot usa o Hub de Afiliados (que já recomenda ofertas), então esta lista é **secundária**. Útil para futuras expansões.

---

### `/hot_list`
Lista todas as palavras-chave ativas.

**Uso:**
```
/hot_list
```

**Retorna:**
```
🔥 Palavras-chave Ativas:

• iphone
• airpods
• smartwatch
• notebook
```

---

### `/remove_hot [termo]`
Remove uma palavra-chave da lista de busca.

**Uso:**
```
/remove_hot airpods
```

**Retorna:**
```
✅ 'airpods' removido da busca ativa.
```

---

## 🚫 Gerenciamento de Blacklist

### `/block [termo]`
Bloqueia produtos que contenham o termo no título.

**Uso:**
```
/block replica
```

**Retorna:**
```
🚫 'replica' adicionado à blacklist!
```

**Quando usar:**
- Produtos de baixa qualidade (ex: "replica", "genérico")
- Categorias que você não quer promover
- Termos que geram reclamações

**Importante:** A blacklist é **case-insensitive** (não diferencia maiúsculas/minúsculas).

---

### `/block_list`
Lista todos os termos bloqueados.

**Uso:**
```
/block_list
```

**Retorna:**
```
🚫 Termos Bloqueados:

• replica
• generico
• usado
• defeito
```

---

### `/remove_block [termo]`
Remove um termo da blacklist.

**Uso:**
```
/remove_block usado
```

**Retorna:**
```
✅ 'usado' removido da blacklist.
```

---

## 📚 Ajuda

### `/help` ou `/start`
Exibe o guia rápido de comandos.

**Uso:**
```
/help
```

**Retorna:**
```
📖 Guia de Comandos do Bot

🔗 Links Diretos: Basta colar um link no chat para postar.
📊 /status: Resumo de atividade do bot.

🤖 Modo de Operação:
• /auto: Alterna entre modo Manual e Autônomo.

🔥 Busca Ativa (Keywords):
• /hot [termo]: Adiciona produto à busca.
• /hot_list: Lista termos ativos.
• /remove_hot [termo]: Remove termo.

🚫 Segurança (Blacklist):
• /block [termo]: Bloqueia palavras no título.
• /block_list: Lista termos bloqueados.
• /remove_block [termo]: Desbloqueia termo.

💡 Dica: Links manuais são limpos automaticamente após o envio!
```

---

## 🎓 Exemplos de Uso Prático

### Cenário 1: Configuração Inicial
```
1. /status                    # Verifica se está tudo ok
2. /block replica             # Bloqueia produtos ruins
3. /block generico
4. /auto                      # Ativa modo autônomo
```

### Cenário 2: Encontrou uma Oferta Manualmente
```
1. Copia o link do produto
2. Cola no chat com o bot
3. Bot processa e posta automaticamente
```

### Cenário 3: Ajuste Fino de Busca
```
1. /hot_list                  # Vê palavras ativas
2. /remove_hot notebook       # Remove termo que não está funcionando
3. /hot macbook              # Adiciona termo mais específico
4. /scan                     # Força busca imediata
```

### Cenário 4: Supervisão Temporária
```
1. /auto                     # Desativa modo autônomo
2. (Revisa ofertas manualmente por algumas horas)
3. /auto                     # Reativa modo autônomo
```

---

## 🔐 Segurança

- ✅ Apenas o `ADMIN_USER_ID` pode executar comandos
- ✅ Comandos funcionam apenas em chat privado
- ✅ Links manuais são limpos após processamento (não ficam no arquivo)
- ✅ Blacklist protege contra produtos indesejados

---

## 📝 Arquivos de Configuração

Os comandos modificam os seguintes arquivos:

| Arquivo | Comandos Relacionados | Descrição |
|---------|----------------------|-----------|
| `data/hot_keywords.txt` | `/hot`, `/hot_list`, `/remove_hot` | Lista de palavras-chave |
| `data/blacklist.txt` | `/block`, `/block_list`, `/remove_block` | Termos bloqueados |
| `data/manual_links.txt` | `/add`, colar link | Links para processamento |
| `data/bot_config.json` | `/auto` | Estado do modo autônomo |

**Nota:** Você pode editar esses arquivos manualmente se preferir, mas use os comandos para garantir formatação correta.

---

## 🆘 Troubleshooting

### "O bot não responde aos comandos"
- ✅ Verifique se você é o `ADMIN_USER_ID` configurado no `.env`
- ✅ Confirme que está enviando no chat **privado** (não em grupo)
- ✅ Reinicie o bot: `Ctrl+C` e `python main.py`

### "Modo autônomo não está postando"
- ✅ Verifique se há ofertas com score > 60 (use logs)
- ✅ Confirme que o modo está ativo: `/status`
- ✅ Aguarde o próximo ciclo de busca (30 min) ou force com `/scan`

### "Blacklist não está funcionando"
- ✅ Termos são case-insensitive: "REPLICA" = "replica"
- ✅ Use termos simples (evite frases complexas)
- ✅ Verifique a lista: `/block_list`

---

## 🚀 Próximos Passos

Agora que você conhece todos os comandos:

1. Configure sua blacklist inicial
2. Ative o modo autônomo se quiser operação 24/7
3. Monitore os logs em `logs/bot.log`
4. Ajuste os pesos de scoring em `core/scoring.py` se necessário

**Dúvidas?** Consulte o [README.md](../README.md) ou abra uma issue no repositório.
