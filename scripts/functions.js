const parseTime = d3.timeParse("%Y-%m-%d %H:%M:%S.%L")

const formatTime = (date) => {
    var minutes = date.getMinutes().toString().padStart(2, '0');
    var seconds = date.getSeconds().toString().padStart(2, '0');
    var milliseconds = date.getMilliseconds().toString().padStart(3, '0');
    return `${minutes}:${seconds}:${milliseconds}`;
}