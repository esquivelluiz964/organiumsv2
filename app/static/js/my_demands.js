class MyDemandsManager {
    constructor() {
        this.kanbanContainer = document.getElementById("kanbanContainer");
        this.emptyState = document.getElementById("emptyState");
        this.kanbanSelector = document.getElementById("kanbanSelector");
        
        console.log("MyDemandsManager inicializado");
        console.log("Dados disponíveis:", myKanbanData);
        console.log("User ID:", currentUserId);
        
        this.registerEvents();
        this.setupModal(); // Configurar o modal
    }

    registerEvents() {
        // Evento do seletor de quadro
        if (this.kanbanSelector) {
            this.kanbanSelector.addEventListener("change", (e) => {
                this.loadMyKanban(e.target.value);
            });
        }
    }

    setupModal() {
        // Fechar modal ao clicar no X
        const closeBtn = document.querySelector('#cardModal .close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeModal();
            });
        }

        // Fechar modal ao clicar fora
        const modal = document.getElementById('cardModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal();
                }
            });
        }

        // Fechar modal com ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    closeModal() {
        const modal = document.getElementById('cardModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    loadMyKanban(boardId) {
        console.log("Carregando quadro:", boardId);
        
        if (!boardId || boardId === "") {
            this.showEmptyState("Selecione um quadro para visualizar suas demandas");
            return;
        }

        const board = myKanbanData.find(b => b.id == boardId);
        if (!board) {
            this.showEmptyState("Quadro não encontrado");
            return;
        }

        this.renderMyKanban(board);
    }

    renderMyKanban(board) {
        console.log("Renderizando quadro:", board);
        
        this.emptyState.style.display = "none";
        this.kanbanContainer.innerHTML = "";

        if (board.columns.length === 0) {
            this.showEmptyState("Nenhuma demanda encontrada para você neste quadro");
            return;
        }

        const boardEl = document.createElement("div");
        boardEl.classList.add("kanban-board");
        boardEl.id = `kanban-${board.id}`;
        
        board.columns.forEach(column => {
            const columnEl = this.createColumnEl(column);
            boardEl.appendChild(columnEl);
        });

        this.kanbanContainer.appendChild(boardEl);
    }

    createColumnEl(column) {
        const columnEl = document.createElement("div");
        columnEl.classList.add("kanban-column");
        columnEl.dataset.columnId = column.id;
        columnEl.style.borderLeft = `4px solid ${column.color}`;

        const translatedName = this.translateColumnName(column.name);
        
        columnEl.innerHTML = `
            <div class="kanban-column-header">
                <h3 class="kanban-column-title">${translatedName}</h3>
                <span class="card-count">${column.cards.length} card(s)</span>
            </div>
            <div class="kanban-cards" data-column-id="${column.id}">
                ${column.cards.length > 0 ? 
                  column.cards.map(card => this.createCardEl(card)).join('') : 
                  '<div class="empty-card">Nenhum card</div>'
                }
            </div>
        `;

        return columnEl;
    }

    createCardEl(card) {
        const gutScore = card.gravidade * card.urgencia * card.tendencia;
        const gutClass = this.getGUTClass(gutScore);
        const today = new Date();
        const prazoDate = card.prazo ? new Date(card.prazo) : null;
        const isLate = prazoDate && prazoDate < today;
        
        const isResponsible = card.responsavel && card.responsavel.user_id == currentUserId;
        const statusText = isResponsible ? '👤 Responsável' : '✍️ Criado por mim';

        return `
            <div class="kanban-card ${gutClass} ${isLate ? 'prazo-atrasado' : ''}" 
                 onclick="openCardDetails(${card.id})" 
                 data-card-id="${card.id}">
                <div class="kanban-card-header">
                    <h4 class="kanban-card-title">${this.escapeHtml(card.title)}</h4>
                    <span class="gut-badge">GUT: ${gutScore}</span>
                </div>
                <div class="kanban-card-content">
                    <p>${card.description ? this.escapeHtml(card.description.substring(0, 100)) + '...' : 'Sem descrição'}</p>
                    <div class="kanban-card-meta">
                        <small>Prazo: ${prazoDate ? prazoDate.toLocaleDateString('pt-BR') : 'Sem prazo'}</small>
                        <br>
                        <small>${statusText}</small>
                    </div>
                </div>
            </div>
        `;
    }

    translateColumnName(name) {
        const translations = {
            'Backlog': 'Pendências',
            'To Do': 'A Fazer', 
            'Doing': 'Fazendo',
            'Done': 'Concluído'
        };
        return translations[name] || name;
    }

    getGUTClass(score) {
        if (score >= 64) return 'gut-critical';
        if (score >= 27) return 'gut-high';
        if (score >= 8) return 'gut-medium';
        return 'gut-low';
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showEmptyState(msg = "Selecione um quadro para visualizar suas demandas") {
        this.kanbanContainer.innerHTML = "";
        this.emptyState.style.display = "block";
        this.emptyState.innerHTML = `<p>${msg}</p>`;
    }
}

// Função global para abrir detalhes do card
function openCardDetails(cardId) {
    console.log("Abrindo detalhes do card:", cardId);
    
    let cardData = null;
    
    for (const board of myKanbanData) {
        for (const column of board.columns) {
            const card = column.cards.find(c => c.id === cardId);
            if (card) {
                cardData = card;
                break;
            }
        }
        if (cardData) break;
    }
    
    if (cardData) {
        const gutScore = cardData.gravidade * cardData.urgencia * cardData.tendencia;
        const prazoDate = cardData.prazo ? new Date(cardData.prazo) : null;
        
        document.getElementById('cardDetails').innerHTML = `
            <div class="card-details">
                <h3>${cardData.title}</h3>
                
                <div class="detail-section">
                    <h4>📋 Descrição</h4>
                    <p>${cardData.description || 'Nenhuma descrição fornecida'}</p>
                </div>
                
                <div class="detail-section">
                    <h4>🎯 O que fazer</h4>
                    <p>${cardData.o_que_fazer || 'Não especificado'}</p>
                </div>
                
                <div class="detail-grid">
                    <div class="detail-item">
                        <strong>📍 Onde:</strong>
                        <span>${cardData.onde_fazer || 'Não especificado'}</span>
                    </div>
                    <div class="detail-item">
                        <strong>⏰ Prazo:</strong>
                        <span>${prazoDate ? prazoDate.toLocaleDateString('pt-BR') : 'Sem prazo'}</span>
                    </div>
                    <div class="detail-item">
                        <strong>👤 Responsável:</strong>
                        <span>${cardData.responsavel ? cardData.responsavel.name : 'Não atribuído'}</span>
                    </div>
                    <div class="detail-item">
                        <strong>🏢 Setor:</strong>
                        <span>${cardData.setor ? cardData.setor.name : 'Não especificado'}</span>
                    </div>
                </div>
                
                <div class="gut-criteria">
                    <h4>📊 Critérios GUT</h4>
                    <div class="gut-scores">
                        <div class="gut-score-item">
                            <span class="gut-label">Gravidade:</span>
                            <span class="gut-value">${cardData.gravidade}/5</span>
                        </div>
                        <div class="gut-score-item">
                            <span class="gut-label">Urgência:</span>
                            <span class="gut-value">${cardData.urgencia}/5</span>
                        </div>
                        <div class="gut-score-item">
                            <span class="gut-label">Tendência:</span>
                            <span class="gut-value">${cardData.tendencia}/5</span>
                        </div>
                        <div class="gut-total">
                            <strong>Pontuação Total GUT: ${gutScore}</strong>
                        </div>
                    </div>
                </div>
                
                <div class="card-meta">
                    <small>Criado por: ${cardData.criador.name}</small>
                    <small>Em: ${new Date(cardData.created_at).toLocaleDateString('pt-BR')}</small>
                </div>
            </div>
        `;
        
        document.getElementById('cardModal').style.display = 'block';
    } else {
        alert('Card não encontrado!');
    }
}

// Função global para fechar modal (mantida para compatibilidade com HTML)
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    console.log("Inicializando MyDemandsManager...");
    window.myDemandsManager = new MyDemandsManager();
});