# Validação do lançador Caxy

- HTML aberto por `file://` no Chromium, com seleção da pasta pelo navegador.
- Introdução e menu renderizados; áudio da introdução medido com AudioContext em estado running e sinal PCM variável.
- Python: clique em Começar com som inicializa o contexto antes de carregar o runtime. Testado com restrição de autoplay habilitada.
- Sequência do livro: o recurso de som PEDESTAL.AIF está embutido em BASICA81.DXR. O motor acionou o membro 519 do cast 1 no canal 2, volume 128, e houve sinal no áudio do navegador ao entrar diretamente na sequência para o teste.
- O percurso completo até coletar o livro pelo mouse não foi confirmado; não declarar esse problema completamente resolvido.
- Esc: o script original teclado compara keyCode com 53 (Escape) e chama play para o filme menu. Retornar ao menu é comportamento previsto.

As requisições HTTPS dos assets no teste HTML usaram dados obtidos com TLS verificado; o navegador de teste não tinha a CA do proxy deste ambiente. Isso não muda o HTML distribuído, que carrega os assets pelo HTTPS normal do navegador do usuário.

A maioria das fases não foi testada. Nenhum arquivo original do jogo é incluído neste repositório.
