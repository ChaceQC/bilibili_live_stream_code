import { reactive } from 'vue';

const state = reactive({ logs: [] });

const log = (msg) => {
  // 如果 msg 是对象，尝试转字符串，避免 [object Object]
  if (typeof msg === 'object') {
    try {
      msg = JSON.stringify(msg);
    } catch (e) {
      msg = String(msg);
    }
  }
  const time = new Date().toLocaleTimeString();
  // 修改为 push，最新的在最下面
  state.logs.push(`[${time}] ${msg}`);
  
  // 限制日志数量，防止内存溢出
  if (state.logs.length > 500) {
    state.logs.shift();
  }
};

// 暴露给后端调用
window.onBackendLog = (msg) => {
  log(msg);
};

// 等待 pywebview 就绪的 Promise
const waitPywebview = new Promise((resolve) => {
  if (window.pywebview) {
    resolve();
  } else {
    window.addEventListener('pywebviewready', () => resolve());
    setTimeout(() => resolve(), 3000);
  }
});

const callPy = async (funcName, ...args) => {
  await waitPywebview;
  if (window.pywebview) {
    try {
      return await window.pywebview.api[funcName](...args);
    } catch (e) {
      console.error(`[Py Error] ${funcName}:`, e);
      return { code: -1, msg: `Python执行错误: ${e}` };
    }
  } else {
    console.warn(`[Mock] Call: ${funcName}`, args);
    if (funcName === 'get_window_position') return { x: 100, y: 100 }; // Mock for browser
    return { code: -1, msg: "Python 后端未连接 (请通过 main.py 启动)" };
  }
};

export const useBridge = () => {
  return {
    state,

    // 窗口拖拽
    async getWindowPosition() {
      return await callPy('get_window_position');
    },
    windowDrag(targetX, targetY) {
      callPy('window_drag', targetX, targetY);
    },

    // 加载配置
    async loadSavedConfig() {
      const res = await callPy('load_saved_config');
      return res.code === 0 ? res.data : {};
    },

    // 刷新当前用户信息
    async refreshCurrentUser() {
      const res = await callPy('refresh_current_user');
      return res.code === 0 ? res.data : null;
    },

    // 扫码登录
    async getLoginQrcode() {
      const res = await callPy('get_login_qrcode');
      return res.code === 0 ? res.data : null;
    },
    async pollLoginStatus(key) {
      return await callPy('poll_login_status', key);
    },

    // 登录
    async login(form) {
      log('正在验证登录...');
      const res = await callPy('login', form.roomId, form.cookie, form.csrf);
      if (res.code === 0) {
        log(`登录成功: ${res.data.uname}`);
        return { success: true, data: res.data };
      } else {
        log(`登录失败: ${res.msg}`);
        return { success: false, msg: res.msg };
      }
    },

    async getPartitions() {
      const res = await callPy('get_partitions');
      return res.code === 0 ? res.data : {};
    },

    async updateSettings(type, val1, val2) {
      log(`正在更新${type}...`);
      let res;
      if (type === 'title') {
        res = await callPy('update_title', val1);
      } else {
        res = await callPy('update_area', val1, val2);
      }

      if (res.code === 0) {
        log(`${type} 更新成功`);
        return { success: true };
      } else {
        log(`${type} 更新失败: ${res.msg}`);
        return { success: false, msg: res.msg };
      }
    },

    async toggleLive(isStarting, p_name, s_name) {
      if (isStarting) {
        log('正在获取推流码...');
        // 传递分区参数给后端
        const res = await callPy('start_live', p_name, s_name);
        if (res.code === 0) {
          log('获取成功，已开播！');
          return { success: true, data: res.data };
        } else if (res.code === 60024) {
          log('⚠️ 需要人脸验证');
          return { success: false, needFaceVerify: true, qrUrl: res.qr };
        } else {
          log(`开播失败: ${res.msg}`);
          return { success: false, msg: res.msg };
        }
      } else {
        log('正在停止直播...');
        const res = await callPy('stop_live');
        if (res.code === 0) {
          log('直播已停止');
          return { success: true };
        } else {
          log(`停止失败: ${res.msg}`);
          return { success: false, msg: res.msg };
        }
      }
    },

    // 账户管理接口
    async getAccountList() {
      const res = await callPy('get_account_list');
      return res.code === 0 ? res.data : { list: [], current_uid: null };
    },

    async switchAccount(uid) {
      const res = await callPy('switch_account', uid);
      return res.code === 0 ? { success: true, data: res.data } : { success: false, msg: res.msg };
    },

    async logout(uid) {
      const res = await callPy('logout', uid);
      return res.code === 0;
    },

    // 窗口控制接口
    async windowControl(action) {
      if (action === 'min') await callPy('window_min');
      else if (action === 'max') {
        const res = await callPy('window_max');
        return res.is_maximized;
      }
      else if (action === 'close') await callPy('window_close');
    },

    // 弹幕监控接口
    async startDanmuMonitor() {
      return await callPy('start_danmu_monitor');
    },
    async stopDanmuMonitor() {
      return await callPy('stop_danmu_monitor');
    },
    
    // 发送弹幕
    async sendDanmu(msg) {
      const res = await callPy('send_danmu', msg);
      return res;
    }
  };
};
