const libMath = module.exports = {
    /*
     * Checks point is correct
     * @param point point
     * @return boolean
     */
    isPoint: point => point && typeof point[0] === "number" && typeof point[1] === "number" &&
        typeof point[2] === "number" && point[0] % 1 === 0 && point[1] % 1 === 0 && point[2] % 1 === 0,

    /*
     * Checks float point is correct
     * @param point point
     * @return boolean
     */
    isFloatPoint: point => point && typeof point[0] === "number" && typeof point[1] === "number" &&
        typeof point[2] === "number",

    /*
     * Checks float area is correct
     * @param area area
     * @return boolean
     */
    isFloatArea: area => area && libMath.isFloatPoint(area[0]) && libMath.isFloatPoint(area[1]),

    /*
     * Checks area is correct
     * @param area area
     * @return boolean
     */
    isArea: area => area && libMath.isPoint(area[0]) && libMath.isPoint(area[1]),

    /*
     * Checks number is in segment
     * @param integer num
     * @param segment [s1, s2]
     * @return boolean
     */
    isInSegment: (num, [s1, s2]) => (s1 <= num && num <= s2) || (s2 <= num && num <= s1),

    /*
     * Checks point is in area
     * @param point [x, y, z]
     * @param area [[ax1, ay1, az1], [ax2, ay2, az2]]
     * @return boolean
     */
    isPointInArea: ([x, y, z], [[ax1, ay1, az1], [ax2, ay2, az2]]) => libMath.isInSegment(x, [ax1, ax2]) &&
        libMath.isInSegment(y, [ay1, ay2]) && libMath.isInSegment(z, [az1, az2]),

    /*
     * Checks area is in area
     * @param area [point1, point2]
     * @param area outerArea
     * @return boolean
     */
    isSubarea: ([point1, point2], outerArea) => libMath.isPointInArea(point1, outerArea) && libMath.isPointInArea(point2, outerArea),

    /*
     * Adds vector to vector
     * @param vector [x1, y1, z1]
     * @param vector [x2, y2, z2]
     * @return vector
     */
    sum: ([x1, y1, z1], [x2, y2, z2]) => [x1 + x2, y1 + y2, z1 + z2],

    /*
     * Multiplies vector by vector
     * @param vector [x1, y1, z1]
     * @param vector [x2, y2, z2]
     * @return vector
     */
    mul: ([x1, y1, z1], [x2, y2, z2]) => [Math.floor(x1 * x2), Math.floor(y1 * y2), Math.floor(z1 * z2)],

    /*
     * Multipies vector by number
     * @param vector [x, y, z]
     * @param integer n
     * @return vector
     */
    mulNumber: ([x, y, z], n) => [Math.floor(x * n), Math.floor(y * n), Math.floor(z * n)],

    /*
     * Moves area by vector
     * @param area [point1, point2]
     * @param vector vector
     */
    moveArea: ([point1, point2], vector) => [libMath.sum(point1, vector), libMath.sum(point2, vector)],

    /*
     * Gets area size
     * @param area [[ax1, ay1, az1], [ax2, ay2, az2]]
     * @return point
     */
    getAreaSize: ([[ax1, ay1, az1], [ax2, ay2, az2]]) =>
        [Math.abs(ax1 - ax2) + 1, Math.abs(ay1 - ay2) + 1, Math.abs(az1 - az2) + 1],

    /*
     * Makes area points min and max of original area
     * @param area [[ax1, ay1, az1], [ax2, ay2, az2]]
     * @return area
     */
    normalizeArea: ([[ax1, ay1, az1], [ax2, ay2, az2]]) =>
        [[Math.min(ax1, ax2), Math.min(ay1, ay2), Math.min(az1, az2)],
        [Math.max(ax1, ax2), Math.max(ay1, ay2), Math.max(az1, az2)]],

    /*
     * Makes new segment based on normal segment and fraction of scaler
     * @param segment [a1, a2]
     * @param segment [s1, s2]
     * @return segment
     */
    refitNormalSegment: ([a1, a2], [s1, s2]) =>
        [Math.floor(a1 + s1 * (a2 - a1)), Math.floor(a1 + s2 * (a2 - a1))],

    /* Makes new area based on area and fraction of scaler
     * @param area area
     * @param area scaler
     * @return area
     */
    refitArea: (area, scaler) => {
        const [[ax1, ay1, az1], [ax2, ay2, az2]] = libMath.normalizeArea(area);
        const [[sx1, sy1, sz1], [sx2, sy2, sz2]] = libMath.normalizeArea(scaler);

        return [
            [Math.floor(ax1 + sx1 * (ax2 - ax1)), Math.floor(ay1 + sy1 * (ay2 - ay1)),
            Math.floor(az1 + sz1 * (az2 - az1))],

            [Math.floor(ax1 + sx2 * (ax2 - ax1)), Math.floor(ay1 + sy2 * (ay2 - ay1)),
            Math.floor(az1 + sz2 * (az2 - az1))]
        ];
    }
};