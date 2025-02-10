# 哔哩哔哩推流码获取工具
1. 用于在准备直播时获取第三方推流码，以便可以绕开哔哩哔哩直播姬，直接在如OBS等软件中进行直播，软件同时提供定义直播分区和标题功能
2. 适用于使用第三方推流直播而不想使用哔哩哔哩直播姬的人群。

## 声明

1. 本程序仅用于获取推流地址以及推流码，不会封号等等，任何与账号有关的问题概不负责。

## 使用教程

### 手动获取 Cookie

1. 登录自己的哔哩哔哩网页客户端。
2. 进入自己的直播间。
3. 点击 ***F12*** 进入开发者模式，选择网络一栏。
4. 给自己发送任意一条弹幕（不开播也可以发）。
5. 在网络一栏找到名为 ***send*** 的一条，点击。
6. 在标头中找到请求标头中的 ***Cookie*** ，在负载中找到表单数据的 ***csrf*** ，分别复制下来。
7. 获取自己直播间的 ID（在个人中心-我的直播间-开播设置中可找到）。
8. 打开程序，按要求输入所需的值（直播间ID即为 ***room_id*** ）。
9. 设置标题和分区。
10. 在 OBS 中输入直播的服务器以及推流码然后开播即可。

### 自动获取 Cookie

1. 扫码登录。
2. 设置标题和分区。
3. 在 OBS 中输入直播的服务器以及推流码然后开播即可。

## 注意事项

1. **一定要使用本程序下播，OBS 停止直播不会下播！！！（非常重要！！！！）**
2. 如果误关了程序，再进行一遍上述操作即可。
3. 获取的推流码仅可使用一次，再次直播时需重新获取。
4. 保存的 Cookies 在一定时间内可重复使用（问就是我也不知道多久），若失效就再进行一遍上述操作即可。
5. 自动获取 Cookie 时，注意不要将鼠标一直停留在网页，成功登录后就移除，否则可能导致获取失败！
6. 如登录后无反应，请将鼠标移动至头像处即可。

## 其他

1. 本程序作者：Chace。  
2. 本程序制作特别感谢：琴子。
