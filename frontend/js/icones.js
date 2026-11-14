// Ícones em SVG (traço 1.75, 20x20), sem dependências externas.
const caminhos = {
  painel: '<rect x="3" y="3" width="6" height="7" rx="1"/><rect x="11" y="3" width="6" height="4" rx="1"/><rect x="11" y="9" width="6" height="8" rx="1"/><rect x="3" y="12" width="6" height="5" rx="1"/>',
  lancamentos: '<path d="M3 5h14M3 10h14M3 15h14"/><path d="M7 3v14"/>',
  cartao: '<rect x="2.5" y="4.5" width="15" height="11" rx="1.5"/><path d="M2.5 8.5h15M6 12.5h3"/>',
  orcamento: '<circle cx="10" cy="10" r="7"/><path d="M10 3v7l5 4.5"/>',
  assinaturas: '<path d="M15.5 7.5A6 6 0 0 0 4.6 6M4.5 12.5A6 6 0 0 0 15.4 14"/><path d="M15.5 3.5v4h-4M4.5 16.5v-4h4"/>',
  objetivos: '<circle cx="10" cy="10" r="7"/><circle cx="10" cy="10" r="3.5"/><circle cx="10" cy="10" r=".6" fill="currentColor"/>',
  categorias: '<path d="M3 4.5h5l1.5 2H17v9H3z"/>',
  conta: '<circle cx="10" cy="7" r="3.2"/><path d="M3.5 17c1.2-3 3.6-4.5 6.5-4.5s5.3 1.5 6.5 4.5"/>',
  sair: '<path d="M8 4H4v12h4M12 6.5 15.5 10 12 13.5M15.5 10H7.5"/>',
  mais: '<path d="M10 4v12M4 10h12"/>',
  editar: '<path d="M12.5 4.5l3 3L7 16H4v-3z"/>',
  lixeira: '<path d="M4 6h12M8 6V4h4v2M5.5 6l.8 10h7.4l.8-10"/>',
  esquerda: '<path d="M12 4.5 6.5 10l5.5 5.5"/>',
  direita: '<path d="M8 4.5 13.5 10 8 15.5"/>',
  baixar: '<path d="M10 3.5v9M6 9l4 4 4-4M4 16.5h12"/>',
  copiar: '<rect x="7" y="7" width="9" height="9" rx="1"/><path d="M4 13V4h9"/>',
  raio: '<path d="M11 2.5 4.5 11H10l-1 6.5 6.5-8.5H10z"/>',
  pausar: '<path d="M7.5 5v10M12.5 5v10"/>',
  tocar: '<path d="M6.5 4.5v11l9-5.5z"/>',
  fechar: '<path d="M5 5l10 10M15 5 5 15"/>',
  rede: '<path d="M3 10h3l2-5 4 10 2-5h3"/>',
  porquinho: '<path d="M4 10.5c0-3 2.7-5 6-5 2.2 0 3.6.6 4.6 1.6l1.9-.6-.4 2.5c.6.7.9 1.5.9 2.4 0 2.2-1.6 3.5-3 4.1V17h-2.5v-1.2H9V17H6.5v-1.6C5 14.6 4 12.8 4 10.5z"/><circle cx="13.2" cy="9.6" r=".6" fill="currentColor"/>',
  busca: '<circle cx="9" cy="9" r="5"/><path d="m13 13 3.5 3.5"/>',
  relogio: '<circle cx="10" cy="10" r="7"/><path d="M10 6v4l2.5 2"/>',
};

export function icone(nome, rotulo = "") {
  const acessibilidade = rotulo ? `role="img" aria-label="${rotulo}"` : 'aria-hidden="true"';
  return `<svg class="icone" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" ${acessibilidade}>${caminhos[nome] || ""}</svg>`;
}
