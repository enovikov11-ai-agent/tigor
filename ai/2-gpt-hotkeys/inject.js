(async () => {
   const items = {
      3: { selector: ".text-sm", text: "GPT-3.5" },
      4: { selector: ".text-sm", text: "GPT-4" },
      N: { selector: "nav .truncate", mod(i) { i.innerText += " [N, H]" } },
      E: { selector: "header [data-state] button" },
      C: { selector: "[role=dialog] .btn-primary div, .btn-primary[to], .btn-danger div" },
      B: { selector: "[role=dialog] .btn-neutral div" },
      M: { selector: "nav .border-t button .font-semibold" },
      T: { selector: "label div" },
      P: { selector: "a", text: "Мой план" },
      I: { selector: "a", text: "Индивидуальные инструкции" },
      S: { selector: "a", text: "Настройки и бета-версия" },
      H: {
         click() {
            localStorage['oai/apps/historyDisabled'] = localStorage['oai/apps/historyDisabled'] === '"true"' ? '"false"' : '"true"';
            location.reload();
         }
      }
   };

   // Add keyboard navigation hint
   new MutationObserver(() => {
      for (let key in items) {
         if (items[key].click) { continue; }
         const item = items[key],
            nodes = [...document.querySelectorAll(item.selector)].filter(i => !item.text || i.innerText === item.text);

         if (nodes.length === 1 && item.node !== nodes[0]) {
            item.node = nodes[0];

            if (item.mod) {
               item.mod(item.node);
            } else if (item.node.childElementCount > 0) {
               item.node.appendChild(document.createTextNode(` [${key}]`))
            } else {
               item.node.innerText += ` [${key}]`;
            }
         }
      }
   }).observe(document.body, { attributes: false, childList: true, subtree: true });

   // Press button if corresponding key pressed
   document.addEventListener("keypress", ({ target, key }) => {
      if (target.tagName === "TEXTAREA") { return; }
      items[key.toUpperCase()]?.node?.click?.();
      items[key.toUpperCase()]?.click?.();
   })
})();
