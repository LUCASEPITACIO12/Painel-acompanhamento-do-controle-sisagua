/* Versão mínima, para o GitHub Pages, da parte do painel de dados do Claude que painel/index.html usa:
   dash.loader, dash.calc, dash.data, dash.onData, dash.draw, dash.params, dash.setParams e dash.resetParams. */
(function () {
  const loaders = {}, calcs = {}, desenhos = new Map(), ouvintes = [], fontes = {};
  let padrao = {}, params = {}, cache = {};

  function dado(id) {
    if (id in cache) return cache[id];
    let r;
    if (calcs[id]) {
      const entradas = calcs[id].inputs.map(dado);
      const pendente = entradas.find((x) => x.status !== 'ok');
      if (pendente) r = {status: pendente.status === 'error' ? 'error' : 'loading', data: null};
      else {
        try { r = {status: 'ok', data: calcs[id].fn(...entradas.map((x) => x.data))}; }
        catch (e) { console.error(`Cálculo ${id}:`, e); r = {status: 'error', data: null, message: String(e)}; }
      }
    } else r = fontes[id] || {status: 'missing', data: []};
    return (cache[id] = r);
  }

  function desenhar(nome) {
    const d = desenhos.get(nome);
    for (const el of document.querySelectorAll(`[data-draw="${nome}"]`)) {
      if (el.closest('[hidden]')) continue; // como no Claude: nada escondido é desenhado
      try {
        if (typeof d === 'function') d(el);
        else {
          if (!d.feitos.has(el)) { el.replaceChildren(); d.feitos.set(el, d.mount ? d.mount(el) : undefined); }
          if (d.update) d.update(el, d.feitos.get(el));
        }
      } catch (e) { console.error(`Desenho ${nome}:`, e); }
    }
  }

  function redesenhar() {
    cache = {};
    for (const f of ouvintes) { try { f(); } catch (e) { console.error(e); } }
    for (const nome of desenhos.keys()) desenhar(nome);
  }

  window.dash = {
    loader: (id, o) => { loaders[id] = o.fn; },
    calc: (id, o) => { calcs[id] = o; },
    data: dado,
    onData: (f) => { ouvintes.push(f); },
    draw: (nome, d) => {
      if (d === undefined) return desenhar(nome);
      desenhos.set(nome, typeof d === 'function' ? d : {...d, feitos: new WeakMap()});
    },
    params: () => ({...params}),
    setParams: (p) => { params = {...params, ...p}; redesenhar(); },
    resetParams: () => { params = {...padrao}; redesenhar(); },
    setLink: () => {},
    colors: ['#1f6fae', '#e07b39'],
    // Busca os arquivos de dados e desenha a página
    iniciar: (arquivos, parametros) => {
      padrao = {...parametros};
      params = {...parametros};
      for (const id of Object.keys(arquivos)) fontes[id] = {status: 'loading', data: []};
      redesenhar();
      for (const [id, url] of Object.entries(arquivos)) {
        fetch(url)
          .then((resp) => { if (!resp.ok) throw new Error(`${url}: ${resp.status}`); return resp.json(); })
          .then((json) => {
            const r = loaders[id] ? loaders[id]({answer: json}) : {data: json};
            fontes[id] = {status: 'ok', data: r.data, columns: r.columns};
          })
          .catch((e) => { console.error(e); fontes[id] = {status: 'error', data: [], message: String(e)}; })
          .finally(redesenhar);
      }
      let espera;
      addEventListener('resize', () => { clearTimeout(espera); espera = setTimeout(redesenhar, 150); });
    },
  };
})();
