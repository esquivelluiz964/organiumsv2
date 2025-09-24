class KanbanManager {
    constructor() {
        this.currentKanban = null;
        this.kanbanContainer = document.getElementById("kanbanContainer");
        this.emptyState = document.getElementById("emptyState");
        this.kanbanSelector = document.getElementById("kanbanSelector");

        // Eventos globais
        this.registerGlobalListeners();

        // Se houver selector, conecta o evento de mudança
        if (this.kanbanSelector) {
            this.kanbanSelector.addEventListener("change", (e) => {
                this.loadKanban(e.target.value);
            });
        }
    }

    /**
     * Carrega um quadro Kanban pelo ID
     */
    async loadKanban(boardId) {
        if (!boardId) {
            this.showEmptyState();
            return;
        }

        try {
            const response = await fetch(`/client/kanban/${boardId}/data`);
            if (!response.ok) throw new Error("Erro ao carregar quadro");

            const data = await response.json();
            this.renderKanban(data);
            this.currentKanban = data;
        } catch (error) {
            console.error("Erro ao carregar Kanban:", error);
            this.showEmptyState("Falha ao carregar quadro.");
        }
    }

    /**
     * Renderiza o quadro no container
     */
    renderKanban(data) {
        this.emptyState.style.display = "none";
        this.kanbanContainer.innerHTML = "";

        data.columns.forEach((column) => {
            const columnEl = document.createElement("div");
            columnEl.classList.add("kanban-column");
            columnEl.dataset.id = column.id;

            const header = document.createElement("h3");
            header.textContent = column.name;
            columnEl.appendChild(header);

            const cardList = document.createElement("div");
            cardList.classList.add("kanban-cards");

            column.cards.forEach((card) => {
                const cardEl = this.renderCard(card);
                cardList.appendChild(cardEl);
            });

            columnEl.appendChild(cardList);

            // Botão para adicionar card
            const addBtn = document.createElement("button");
            addBtn.textContent = "+ Card";
            addBtn.classList.add("btn-small");
            addBtn.addEventListener("click", () => openCardModal(column.id));
            columnEl.appendChild(addBtn);

            this.kanbanContainer.appendChild(columnEl);
        });
    }

    /**
     * Renderiza um card
     */
    renderCard(card) {
        const cardEl = document.createElement("div");
        cardEl.classList.add("kanban-card");
        cardEl.dataset.id = card.id;

        cardEl.innerHTML = `
            <h4>${card.title}</h4>
            <p>${card.description || ""}</p>
            <small>Prazo: ${card.prazo ? new Date(card.prazo).toLocaleDateString() : "-"}</small>
            <div class="kanban-card-actions">
                <button class="btn-edit">✏️</button>
                <button class="btn-delete">🗑️</button>
            </div>
        `;

        // Eventos
        cardEl.querySelector(".btn-edit").addEventListener("click", () => {
            openCardModal(card.column_id, card);
        });

        cardEl.querySelector(".btn-delete").addEventListener("click", () => {
            this.deleteCard(card.id);
        });

        return cardEl;
    }

    /**
     * Deleta um card
     */
    async deleteCard(cardId) {
        if (!confirm("Deseja realmente excluir este card?")) return;

        try {
            const response = await fetch(`/api/kanban/card/${cardId}`, {
                method: "DELETE",
            });
            if (!response.ok) throw new Error("Erro ao excluir card");

            // Remove da tela
            const cardEl = this.kanbanContainer.querySelector(`.kanban-card[data-id="${cardId}"]`);
            if (cardEl) cardEl.remove();
        } catch (error) {
            console.error("Erro ao excluir card:", error);
            alert("Erro ao excluir card.");
        }
    }

    /**
     * Mostra estado vazio
     */
    showEmptyState(msg = "Selecione ou crie um quadro kanban para começar") {
        this.kanbanContainer.innerHTML = "";
        this.emptyState.style.display = "block";
        this.emptyState.textContent = msg;
    }

    /**
     * Listeners globais (como fechar modal clicando fora)
     */
    registerGlobalListeners() {
        window.addEventListener("click", (event) => {
            const modals = document.getElementsByClassName("modal");
            for (let modal of modals) {
                if (event.target === modal) {
                    modal.style.display = "none";
                }
            }
        });
    }
}

// ==========================
// Inicialização
// ==========================
document.addEventListener("DOMContentLoaded", () => {
    window.kanbanManager = new KanbanManager();

    // GUT Score
    ["cardGravidade", "cardUrgencia", "cardTendencia"].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("change", calculateGUTScore);
    });
});

function calculateGUTScore() {
    const gravidade = parseInt(document.getElementById("cardGravidade").value) || 1;
    const urgencia = parseInt(document.getElementById("cardUrgencia").value) || 1;
    const tendencia = parseInt(document.getElementById("cardTendencia").value) || 1;
    const score = gravidade * urgencia * tendencia;
    document.getElementById("gutScore").textContent = score;
}
