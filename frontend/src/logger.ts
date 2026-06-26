/**
 * Copyright 2022 by Open Kilt LLC. All rights reserved.
 * This file is part of the OpenRepo Repository Management Software (OpenRepo)
 * OpenRepo is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License
 * version 3 as published by the Free Software Foundation
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

const isProduction = process.env.NODE_ENV === 'production';

const LEVELS = { debug: 0, info: 1, warn: 2, error: 3 } as const;
type Level = keyof typeof LEVELS;

function log(level: Level, ...args: unknown[]) {
    if (LEVELS[level] < (isProduction ? LEVELS.info : LEVELS.debug)) return;
    const fn = level === 'error' ? console.error : level === 'warn' ? console.warn : level === 'info' ? console.info : console.debug;
    const prefix = `${level.toUpperCase()}|${getCaller()}|`;
    if (typeof args[0] === 'string') {
        fn(prefix + args[0], ...args.slice(1));
    } else {
        fn(prefix, ...args);
    }
}

function getCaller(): string {
    const e = new Error();
    const stack = e.stack?.split('\n');
    // stack[0] = "Error", stack[1] = getCaller, stack[2] = log, stack[3] ≈ caller
    const caller = stack?.[3]?.trim();
    if (caller) {
        const match = caller.match(/at\s+(.+?)\s*\(/) || caller.match(/at\s+(.+)/);
        return match ? match[1] : caller;
    }
    return '';
}

export const logger = {
    debug: (...args: unknown[]) => log('debug', ...args),
    info: (...args: unknown[]) => log('info', ...args),
    warn: (...args: unknown[]) => log('warn', ...args),
    error: (...args: unknown[]) => log('error', ...args),
};
