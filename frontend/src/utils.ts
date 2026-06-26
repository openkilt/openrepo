export function waitFor(conditionFunction: () => boolean, interval = 400): Promise<void> {
    const poll = (resolve: (value: void) => void) => {
        if (conditionFunction()) resolve();
        else setTimeout(() => poll(resolve), interval);
    };
    return new Promise(poll);
}
