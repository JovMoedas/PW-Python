document.addEventListener("DOMContentLoaded", async function() {
    const params = new URLSearchParams(window.location.search);
    const quartoId = params.get("id");

    if (!quartoId) {
        document.body.innerHTML = "<h1>Erro: Nenhum quarto selecionado.</h1>";
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/quarto/${quartoId}`);
        const data = await response.json();

        if (!response.ok || !data || data.error) {
            throw new Error(data.error || "Erro ao buscar quarto.");
        }

        // Verifica se os elementos do HTML existem antes de atribuir valores
        const nomeElemento = document.getElementById("quarto-nome");
        const descricaoElemento = document.getElementById("quarto-descricao");
        const precoElemento = document.getElementById("quarto-preco");
        const imagemElemento = document.getElementById("quarto-imagem");

        if (!nomeElemento || !descricaoElemento || !precoElemento || !imagemElemento) {
            throw new Error("Elementos HTML não encontrados.");
        }

        // Atualiza os detalhes no HTML
        nomeElemento.textContent = data.nome;
        descricaoElemento.textContent = data.descricao;
        precoElemento.textContent = `€${data.preco_noite}`;
        imagemElemento.src = data.imagem;
        imagemElemento.alt = data.nome;

    } catch (error) {
        console.error("Erro ao carregar o quarto:", error);
        document.body.innerHTML = `<h1>Erro ao carregar os detalhes do quarto.</h1><p>${error.message}</p>`;
    }
});