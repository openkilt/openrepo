import semver from 'semver'
import { logger } from '@/logger'

export function formatDate(value: Date): string {
    const d = new Date(value)
    const pad = (n: number) => n.toString().padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export function flagPromotables(pkgsHere: any[], pkgsPromote: any[]): any[] {
    const highestPromotes: Record<string, any> = {}

    pkgsPromote.forEach(pkg => {
        try {
            const curVer = semver.coerce(pkg.version, true)
            if (curVer == null) return
            if (highestPromotes[pkg.package_name] === undefined ||
                semver.gt(curVer, highestPromotes[pkg.package_name], true)) {
                highestPromotes[pkg.package_name] = curVer
            }
        } catch (error) {
            logger.warn(error)
        }
    })

    return pkgsHere.map(pkg => {
        const curVer = semver.coerce(pkg.version, true)
        return {
            ...pkg,
            promotable:
                highestPromotes[pkg.package_name] === undefined ||
                semver.gt(curVer, highestPromotes[pkg.package_name], true),
        }
    })
}

export function buildQueryParams(
    page: number,
    itemsPerPage: number,
    search: string,
    sortColumn: string,
    sortDirection: string,
    extra?: any,
): any {
    const params: any = { page, page_size: itemsPerPage }
    if (search) params.search = search
    params.ordering = (sortDirection === 'desc' ? '-' : '') + sortColumn
    if (extra) Object.assign(params, extra)
    return params
}
