let utils = {
    getHrFieldName: function (fieldName) {
        let segments = fieldName.split(/_+/);

        for (let i = 0; i<segments.length; i++) {
            let segment = segments[i];
            let newSegment = '';

            for (let j = 0; j<segment.length; j++) {
                if (j === 0) {
                    newSegment += segment[j].toUpperCase();
                } else {
                    newSegment += segment[j];
                }
            }

            segments[i] = newSegment;
        }

        return segments.join(' ');
    }
}

export default utils;
