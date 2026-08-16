const inject = document.createElement('script');

inject.src = chrome.runtime.getURL("inject.js");

document.head.appendChild(inject);
