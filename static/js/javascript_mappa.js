let map = L.map('mapid').setView([40.9243453,14.307607], 15);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);


let distributore1 = L.marker([40.9174856,14.3090177]).addTo(map);
popup = distributore1.bindPopup('<b> Distributore acqua</b><br />Via San Francesco, 80021, Afragola.');
let distributore2 = L.marker([40.9194033,14.2990386]).addTo(map);
popup = distributore2.bindPopup('<b> Distributore acqua</b><br />Via Tevere, 80021, Afragola.');
let isolaeco = L.marker([40.9380399,14.3104253]).addTo(map);
popup = isolaeco.bindPopup('<b> Isola Ecologica</b><br />Piazzale Unicef, 80021, Afragola.<br /> 800 993 986');