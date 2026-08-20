# The Footswitch Hardware
Creating this footwitch hardware uses an off-the-shelf footswitch and an Arduino Nano. The 3D-printed enclosure is fixed to the footswitch.
<p align="center">
  <img src="closed_top.jpg" width="20%" title="Footswitch closed top"  alt="Footswitch closed top">
</p>

## Needed Hardware
- Footswitch (TRU COMPONENTS, TC-6648040 [@Conrad.ch](https://www.conrad.ch/de/p/tru-components-fussschalter-250-v-ac-16-a-2-pedale-2-oeffner-2-schliesser-1-st-1662010.html), alternatives are available on [Aliexpress](https://de.aliexpress.com/w/wholesale-double-footswitch.html))
- Arduino Nano
- Pinheaders female for Arduino Nano
- Molex KK 254 header 4 pole angled (Molex 22-05-7048)
- Matching Molex KK 254 connector with crip contacts
- Veroboard (or manufactured PCB)
- Wires
- M3 bolts and nuts

## PCB
The PCB contains the KK 254 connector and the Arduino Nano on pin headers. Four screw holes allow the later mounting on the housing bottom.
The schematic is simple. It just connects D3 through connector and left switch (red) to GND and D4 through connector and right switch (black) to GND.
<p align="center">
  <img src="pcb_schematic.png" width="40%" title="PCB Schematic"  alt="PCB Schematic">
</p>

The PCB can be created using a piece of veroboard and connecting everything. Special attention has to be taken to the nodge for the screw that connects the housing to to footswitch. Here is a picture how it may look like (viewed from top).
<p align="center">
  <img src="pcb_layout.png" width="40%" title="PCB Layout"  alt="PCB Layout">
  <img src="pcb_measurements.png" width="40%" title="PCB Measurements"  alt="PCB Measurements">
</p>


## 3D printed enclosure
The enclosure can be printed and screwed to the footswitch using M3 bolts and nuts. Previeously you have to drill the holes for the M3 bolts using the drilling jig.
<script src="https://embed.github.com/view/3d/grafmar/scope-footswitch-trigger/blob/main/housing/OsciFootswitchHousing_DrillingJig.stl">Drilling Jig</script>

The top of the housing can then be screwed onto the bottom part with M3 bolts
<script src="https://embed.github.com/view/3d/grafmar/scope-footswitch-trigger/blob/main/housing/OsciFootswitchHousing-BaseBodyBottom.stl">OsciFootswitchHousing Bottom</script>
<script src="https://embed.github.com/view/3d/grafmar/scope-footswitch-trigger/blob/main/housing/OsciFootswitchHousing-BaseBodyTop.stl">OsciFootswitchHousing Top</script>


## Buildup
Wires are soldered to the switches, criped and applied to the connector housing to be later connected to the PCB. PCB can be mounted onto the bottom part of the housing. After connecting the USB wire, the wire can be secured with a zip tie as strain relief. And the houseing can be closed
<p align="center">
  <img src="open_angled_view_back.jpg" width="20%" title="Footswitch angled_view_back"  alt="Footswitch angled_view_back">
  <img src="open_bottom.jpg" width="20%" title="Footswitch bottom"  alt="Footswitch bottom">
  <img src="open_USB_connection.jpg" width="20%" title="Footswitch USB_connection"  alt="Footswitch USB_connection">
  <img src="open_top.jpg" width="20%" title="Footswitch top"  alt="Footswitch top">
</p>

