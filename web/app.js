const elements = {
  beacon: document.querySelector('#beacon'),
  morse: document.querySelector('#morse'),
  message: document.querySelector('#message'),
  sender: document.querySelector('#sender'),
  sequence: document.querySelector('#sequence'),
  received: document.querySelector('#received'),
  integrity: document.querySelector('#integrity'),
};

let lastSequence = -1;
let animationGeneration = 0;

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function playMorse(pattern, generation) {
  const unit = 145;
  for (const symbol of pattern) {
    if (generation !== animationGeneration) return;
    if (symbol === '.' || symbol === '-') {
      elements.beacon.classList.add('on');
      await sleep(symbol === '.' ? unit : unit * 3);
      elements.beacon.classList.remove('on');
      await sleep(unit);
    } else if (symbol === ' ') {
      await sleep(unit * 2);
    } else if (symbol === '/') {
      await sleep(unit * 4);
    }
  }
  elements.beacon.classList.remove('on');
}

function render(signal) {
  elements.message.textContent = signal.display;
  elements.sender.textContent = signal.sender;
  elements.sequence.textContent = String(signal.sequence).padStart(4, '0');
  elements.received.textContent = signal.received_at || '--';
  elements.integrity.textContent = signal.integrity;
  elements.morse.textContent = signal.morse;
  if (signal.sequence !== lastSequence && signal.sequence > 0) {
    lastSequence = signal.sequence;
    animationGeneration += 1;
    playMorse(signal.morse, animationGeneration);
  }
}

async function poll() {
  try {
    const response = await fetch('/api/state', {cache: 'no-store'});
    if (!response.ok) throw new Error(`state ${response.status}`);
    render(await response.json());
  } catch (_error) {
    elements.integrity.textContent = 'RECEIVER UNREACHABLE';
  }
}

poll();
setInterval(poll, 650);

