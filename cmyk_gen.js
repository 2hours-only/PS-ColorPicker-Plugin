#target photoshop

(function() {
    var result = [];

    var THRESHOLD = 15; 

    var color = new SolidColor();
    var totalIterations = 180 * 256;
    var currentIteration = 0;

    for (var h_idx = 0; h_idx < 180; h_idx++) {
        color.hsb.hue = h_idx * 2;
        var row = []; 

        for (var s_idx = 0; s_idx < 256; s_idx++) {
            color.hsb.saturation = s_idx * (100 / 255);

            var low = 0.0;
            var high = 100.0;
            var mid;

            for (var i = 0; i < 12; i++) { 
                mid = (low + high) / 2.0;
                color.hsb.brightness = mid;

                var r1 = color.rgb.red;
                var g1 = color.rgb.green;
                var b1 = color.rgb.blue;

                var cmyk = color.cmyk;

                var c2 = new SolidColor();
                c2.cmyk = cmyk;
                var r2 = c2.rgb.red;
                var g2 = c2.rgb.green;
                var b2 = c2.rgb.blue;

                var diff = Math.abs(r1 - r2) + Math.abs(g1 - g2) + Math.abs(b1 - b2);

                if (diff > THRESHOLD) {
                    high = mid; 
                } else {
                    low = mid;  
                }
            }

            row.push(Math.round(low * 2.55));
            currentIteration++;
        }

        result.push(row);
        $.writeln("Completed H_idx: " + h_idx + " (" + (currentIteration/totalIterations*100).toFixed(1) + "%)");
    }

var projectDir = File($.fileName).parent.fsName; 
var file = new File(projectDir + "/asset/cmyk_boundary.bin");

file.encoding = "BINARY";
file.open("w");
for (var h_idx = 0; h_idx < 180; h_idx++) {
    for (var s_idx = 0; s_idx < 256; s_idx++) {
        file.write(String.fromCharCode(result[h_idx][s_idx]));
    }
}
file.close();
alert("✅ 二进制分界线数据已直接覆盖至项目目录：\n" + file.fsName);

})();