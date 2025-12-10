<p align="center">
<img height=300px src="landing/hololens.png" alt="Hololens"></a>
</p>

<h1 align="center">TacticMap</h3>

<div align="center">

[![Unity Version](https://img.shields.io/badge/unity-2019.4.25-blue.svg)][unity]
[![MRTK Version](https://img.shields.io/badge/Microsoft-MRTK%202.6.1-green)][mrtk]
[![GitHub Issues](https://img.shields.io/github/issues/RTUITLab/TacticMap.svg)][issues]

</div>

<p align="center"> 
Project for Microsoft Hololens Mixed Reality headset with multi-user experience.
</p>

---
# Instruction: #

### Unity application configuration: ###
- Open the project in Unity; 
- Download [Photon Pun 2][photon] from asset store;
- Configurete Photon settings;
> `Windows > Photon Unity Networking > Highlight Server Settings` (Ctrl + Shift + Alt + P).
> If the photon server will be used, then you need to enter `App Id PUN` and check the `Use Name Server` box. Else uncheck box and insert ip into `Server` and `Port`. Default port value: 5055.
- Bild Visual Studio solution;
- Deploy on Hololens.

---
### Photon server configuration: ###
- Get ur server [license here][photon license];
- Download [server here][photon server];
- Move license to `../deploy/bin_Win64/`;
- Open PhotonControl.exe;
- Start ur Photon On Premises Server.

---
### Typical problems: ###

> "Windows Mobile" error while building your project: Open `HoloMapOnline > HoloMapOnline.vcxproj` file in the solution folder. At the end of the file, cut out the mention of Windows Mobile.

> "Failed to connect to server after testing each known IP" error: Remove all Win 10 SDK after `10.0.18362` or change unity to a newer LTS version.

[issues]:https://github.com/RTUITLab/TacticMap/issues
[photon]:https://assetstore.unity.com/packages/tools/network/pun-2-free-119922
[photon license]:https://dashboard.photonengine.com/en-US/selfhosted
[photon server]:https://www.photonengine.com/en-us/sdks#server-sdkserverserver
[unity]:https://unity3d.com/get-unity/download
[mrtk]:https://github.com/microsoft/MixedRealityToolkit-Unity/releases/tag/v2.6.1