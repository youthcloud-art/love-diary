<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { auth, request } from "../../api";

type LoginMethod = "password" | "code";
const mode = ref<"login" | "register">("login"), method = ref<LoginMethod>("password");
const phone = ref(""), code = ref(""), password = ref(""), nickname = ref("");
const agreed = ref(true), showPassword = ref(false), showWechat = ref(false), loading = ref(false), seconds = ref(0);
let timer: ReturnType<typeof setInterval> | undefined;
const isRegister = computed(() => mode.value === "register");
const title = computed(() => isRegister.value ? "创建你们的恋爱日记" : "欢迎回到我们的故事");
const submitText = computed(() => loading.value ? "正在轻轻打开…" : isRegister.value ? "注册并开启日记" : method.value === "code" ? "验证并登录" : "登录");
const cleanPhone = () => phone.value.replace(/\s/g, "");
function validPhone(){if(!/^1\d{10}$/.test(cleanPhone())){uni.showToast({title:"请输入正确的 11 位手机号",icon:"none"});return false}return true}
function switchMode(next:"login"|"register"){mode.value=next;method.value=next==="register"?"code":"password";code.value="";password.value=""}
async function sendCode(){
  if(seconds.value||!validPhone())return;
  try{
    const result=await request<{message:string;dev_code?:string}>("/api/v1/auth/code","POST",{phone:cleanPhone()});
    seconds.value=60;timer=setInterval(()=>{seconds.value-=1;if(seconds.value<=0&&timer)clearInterval(timer)},1000);
    uni.showToast({title:result.dev_code?`开发验证码：${result.dev_code}`:result.message,icon:"none",duration:result.dev_code?5000:2000});
  }catch(error){uni.showToast({title:(error as Error).message,icon:"none"})}
}
async function submit(){
  if(!validPhone())return;
  if(!agreed.value){uni.showToast({title:"请先同意用户协议与隐私政策",icon:"none"});return}
  if(isRegister.value&&!nickname.value.trim()){uni.showToast({title:"给自己取一个昵称吧",icon:"none"});return}
  if((isRegister.value||method.value==="code")&&!/^\d{6}$/.test(code.value)){uni.showToast({title:"请输入 6 位验证码",icon:"none"});return}
  if((isRegister.value||method.value==="password")&&password.value.length<6){uni.showToast({title:"密码至少需要 6 位",icon:"none"});return}
  loading.value=true;
  try{
    if(isRegister.value)await auth("phone/register",{phone:cleanPhone(),code:code.value,password:password.value,nickname:nickname.value.trim()});
    else if(method.value==="code")await auth("phone/code-login",{phone:cleanPhone(),code:code.value});
    else await auth("phone/login",{phone:cleanPhone(),password:password.value});
    uni.redirectTo({url:"/pages/space/space"});
  }catch(error){uni.showToast({title:(error as Error).message,icon:"none"})}finally{loading.value=false}
}
function wechatLogin(){
  // #ifdef MP-WEIXIN
  uni.login({success:async result=>{try{await auth("wechat",{code:result.code});uni.redirectTo({url:"/pages/space/space"})}catch(error){uni.showToast({title:(error as Error).message,icon:"none"})}}});
  // #endif
  // #ifdef H5
  showWechat.value=true;
  // #endif
}
onBeforeUnmount(()=>timer&&clearInterval(timer));
</script>

<template>
  <view class="page">
    <view class="glow glow-one"/><view class="glow glow-two"/>
    <view class="floating-heart heart-one">♥</view><view class="floating-heart heart-two">♥</view><view class="floating-heart heart-three">♥</view>
    <view class="brand"><view class="brand-mark">♥</view><text class="brand-name">恋爱日记</text></view>
    <view class="illustration" aria-label="一对相互依偎的恋人插画">
      <view class="moon"/><view class="person person-left"><view class="hair"/><view class="face"><view class="eye"/><view class="blush"/></view><view class="body"/></view>
      <view class="person person-right"><view class="hair"/><view class="face"><view class="eye"/><view class="blush"/></view><view class="body"/></view><view class="love-pulse">♥</view><view class="ground"/>
    </view>
    <view class="welcome"><text class="eyebrow">TWO HEARTS · ONE STORY</text><text class="headline">{{title}}</text><text class="subtitle">把每一个普通日子，都变成值得珍藏的纪念</text></view>
    <view class="card">
      <view class="mode-switch"><view :class="['mode-item',{active:mode==='login'}]" @click="switchMode('login')">登录</view><view :class="['mode-item',{active:mode==='register'}]" @click="switchMode('register')">注册</view></view>
      <view v-if="!isRegister" class="method-tabs"><text :class="{active:method==='password'}" @click="method='password'">密码登录</text><text :class="{active:method==='code'}" @click="method='code'">验证码登录</text></view>
      <view v-if="isRegister" class="field"><text class="field-icon">☺</text><input v-model="nickname" maxlength="20" placeholder="你的昵称" placeholder-class="placeholder"/></view>
      <view class="field"><text class="field-icon">♧</text><text class="phone-prefix">+86</text><view class="divider"/><input v-model="phone" type="number" maxlength="11" placeholder="请输入手机号" placeholder-class="placeholder"/></view>
      <view v-if="isRegister||method==='code'" class="field"><text class="field-icon">✉</text><input v-model="code" type="number" maxlength="6" placeholder="6 位短信验证码" placeholder-class="placeholder"/><button class="code-button" :disabled="seconds>0" @click="sendCode">{{seconds?`${seconds}s`:'获取验证码'}}</button></view>
      <view v-if="isRegister||method==='password'" class="field"><text class="field-icon">⌁</text><input v-model="password" :password="!showPassword" maxlength="32" :placeholder="isRegister?'设置密码（至少 6 位）':'请输入密码'" placeholder-class="placeholder"/><text class="eye-button" @click="showPassword=!showPassword">{{showPassword?'◉':'◎'}}</text></view>
      <view v-if="!isRegister&&method==='password'" class="assist-row"><text class="remember"><text class="check-small">✓</text> 记住我</text><text class="forgot" @click="method='code'">忘记密码？</text></view>
      <button class="primary" :disabled="loading" @click="submit"><text>{{submitText}}</text><text class="arrow">→</text></button>
      <view class="agreement" @click="agreed=!agreed"><view :class="['checkbox',{checked:agreed}]">{{agreed?'✓':''}}</view><text>我已阅读并同意 <text class="link">《用户协议》</text> 和 <text class="link">《隐私政策》</text></text></view>
      <view class="or"><view/><text>其他登录方式</text><view/></view><button class="wechat" @click="wechatLogin"><text class="wechat-icon">●</text><text>微信扫码登录</text></button>
    </view>
    <view class="footer"><text>愿每一次记录，都让爱更有迹可循</text><text class="footer-heart">♥</text></view>
    <view v-if="showWechat" class="modal-mask" @click="showWechat=false"><view class="wechat-modal" @click.stop><text class="modal-close" @click="showWechat=false">×</text><view class="mini-brand"><text>♥</text> 恋爱日记</view><text class="modal-title">微信扫码登录</text><view class="qr-shell"><view class="qr-pattern"><text>▦</text><text>▤</text><text>▥</text><text>▧</text></view><view class="qr-logo">♥</view></view><text class="modal-tip">请使用微信扫一扫</text><text class="modal-note">正式使用前需在服务端配置微信开放平台 AppID</text></view></view>
  </view>
</template>

<style scoped lang="scss">
.page{position:relative;box-sizing:border-box;min-height:100vh;overflow:hidden;padding:54rpx 34rpx 42rpx;background:linear-gradient(155deg,#fffaf7 0%,#fff3ef 48%,#fff8f2 100%);color:#553b3d}.glow{position:absolute;border-radius:50%;filter:blur(4rpx);opacity:.72}.glow-one{width:430rpx;height:430rpx;right:-220rpx;top:80rpx;background:radial-gradient(circle,#ffd7d8 0%,rgba(255,215,216,0) 70%)}.glow-two{width:360rpx;height:360rpx;left:-210rpx;top:540rpx;background:radial-gradient(circle,#ffe1bd 0%,rgba(255,225,189,0) 70%)}.brand{position:relative;z-index:2;display:flex;align-items:center;gap:14rpx}.brand-mark{display:flex;align-items:center;justify-content:center;width:54rpx;height:54rpx;border-radius:18rpx 18rpx 18rpx 6rpx;transform:rotate(-7deg);background:linear-gradient(135deg,#ff8c91,#e85e72);box-shadow:0 12rpx 28rpx rgba(222,90,107,.22);color:#fff;font-size:25rpx}.brand-name{font-family:"STKaiti","KaiTi",serif;font-size:38rpx;font-weight:700;letter-spacing:4rpx;color:#73484d}.illustration{position:relative;width:360rpx;height:250rpx;margin:-10rpx auto -4rpx}.moon{position:absolute;left:62rpx;top:12rpx;width:220rpx;height:220rpx;border-radius:50%;background:linear-gradient(145deg,#fff1d5,#ffd8c8);box-shadow:0 22rpx 60rpx rgba(230,145,139,.15)}.ground{position:absolute;left:30rpx;bottom:14rpx;width:300rpx;height:28rpx;border-radius:50%;background:rgba(193,119,113,.12);filter:blur(4rpx)}.person{position:absolute;bottom:27rpx;width:100rpx;height:142rpx;animation:breathe 3.2s ease-in-out infinite}.person-left{left:92rpx;transform:rotate(5deg);transform-origin:bottom}.person-right{right:86rpx;transform:rotate(-7deg);transform-origin:bottom;animation-delay:-1.5s}.face{position:absolute;z-index:2;left:20rpx;top:15rpx;width:66rpx;height:74rpx;border-radius:48% 48% 45% 45%;background:#ffd8c2}.hair{position:absolute;z-index:3;left:11rpx;top:3rpx;width:80rpx;height:48rpx;border-radius:50% 55% 35% 30%;background:#5b4142;transform:rotate(-5deg)}.person-right .hair{background:#49383a;border-radius:50% 50% 35% 45%;transform:rotate(8deg)}.eye{position:absolute;right:13rpx;top:35rpx;width:7rpx;height:7rpx;border-radius:50%;background:#604447}.person-right .eye{left:13rpx}.blush{position:absolute;right:3rpx;top:48rpx;width:16rpx;height:8rpx;border-radius:50%;background:rgba(244,120,128,.32)}.person-right .blush{left:3rpx}.body{position:absolute;left:4rpx;bottom:0;width:96rpx;height:75rpx;border-radius:48rpx 48rpx 16rpx 16rpx;background:linear-gradient(145deg,#ef8b91,#d96374)}.person-right .body{background:linear-gradient(145deg,#8ea1bd,#697f9f)}.love-pulse{position:absolute;z-index:5;left:170rpx;top:71rpx;color:#f46778;font-size:28rpx;animation:pulse 1.8s ease-in-out infinite}.floating-heart{position:absolute;z-index:1;color:rgba(235,104,121,.38);animation:float 4s ease-in-out infinite}.heart-one{right:110rpx;top:190rpx;font-size:22rpx}.heart-two{left:90rpx;top:330rpx;font-size:16rpx;animation-delay:-1.3s}.heart-three{right:58rpx;top:440rpx;font-size:13rpx;animation-delay:-2.2s}.welcome{position:relative;z-index:2;text-align:center;margin-bottom:34rpx}.eyebrow{display:block;color:#d18b87;font-size:18rpx;font-weight:600;letter-spacing:4rpx}.headline{display:block;margin-top:12rpx;font-family:"STKaiti","KaiTi",serif;font-size:44rpx;font-weight:700;letter-spacing:2rpx;color:#5c3d41}.subtitle{display:block;margin-top:12rpx;color:#a48180;font-size:23rpx}.card{position:relative;z-index:3;padding:12rpx 28rpx 30rpx;border:1rpx solid rgba(255,255,255,.9);border-radius:34rpx;background:rgba(255,255,255,.84);box-shadow:0 28rpx 75rpx rgba(145,83,82,.12);backdrop-filter:blur(20rpx)}.mode-switch{display:flex;margin-bottom:22rpx;border-bottom:1rpx solid #f1dedc}.mode-item{position:relative;flex:1;padding:24rpx 0 20rpx;text-align:center;color:#b29796;font-size:29rpx;font-weight:600}.mode-item.active{color:#d96374}.mode-item.active:after{content:"";position:absolute;left:50%;bottom:-2rpx;width:54rpx;height:5rpx;border-radius:5rpx;transform:translateX(-50%);background:#df6c7b}.method-tabs{display:flex;gap:34rpx;margin:8rpx 0 20rpx;padding-left:4rpx;color:#ad9291;font-size:24rpx}.method-tabs text{padding-bottom:8rpx}.method-tabs .active{color:#c85f70;font-weight:600;border-bottom:3rpx solid #e37b88}.field{display:flex;align-items:center;box-sizing:border-box;height:92rpx;margin-bottom:18rpx;padding:0 22rpx;border:2rpx solid transparent;border-radius:22rpx;background:#fff8f5;transition:.2s}.field:focus-within{border-color:#eea6ad;background:#fff;box-shadow:0 8rpx 24rpx rgba(223,108,123,.08)}.field-icon{width:42rpx;color:#cf777f;font-size:28rpx}.phone-prefix{color:#60484a;font-size:26rpx;font-weight:600}.divider{width:1rpx;height:34rpx;margin:0 20rpx;background:#ead9d7}.field input{flex:1;height:82rpx;color:#563f41;font-size:27rpx}.placeholder{color:#c5afad}.eye-button{padding:18rpx 0 18rpx 18rpx;color:#b89e9d;font-size:27rpx}.code-button{min-width:170rpx;margin:0;padding:0 10rpx;border:0;background:transparent;color:#d96374;font-size:23rpx;line-height:70rpx}.code-button:after{border:0}.code-button[disabled]{background:transparent;color:#cbb8b7}.assist-row{display:flex;justify-content:space-between;margin:-1rpx 4rpx 20rpx;color:#9f8786;font-size:22rpx}.check-small{display:inline-flex;align-items:center;justify-content:center;width:24rpx;height:24rpx;border-radius:7rpx;background:#e47a87;color:#fff;font-size:17rpx}.forgot{color:#d16876}.primary{display:flex;align-items:center;justify-content:center;height:92rpx;margin:22rpx 0 18rpx;border:0;border-radius:24rpx;background:linear-gradient(110deg,#e97582,#d85f73);box-shadow:0 17rpx 32rpx rgba(214,82,105,.24);color:#fff;font-size:29rpx;font-weight:600;letter-spacing:2rpx}.primary:after{border:0}.primary[disabled]{opacity:.68}.arrow{margin-left:18rpx;font-size:34rpx;font-weight:400}.agreement{display:flex;align-items:flex-start;justify-content:center;color:#ad9795;font-size:19rpx;line-height:30rpx}.checkbox{flex:0 0 26rpx;height:26rpx;margin:1rpx 9rpx 0 0;border:2rpx solid #d8c2c0;border-radius:7rpx;text-align:center;color:#fff;font-size:18rpx;line-height:26rpx}.checkbox.checked{border-color:#df7180;background:#df7180}.link{color:#ce6975}.or{display:flex;align-items:center;gap:16rpx;margin:26rpx 0 18rpx;color:#c0abaa;font-size:19rpx}.or view{flex:1;height:1rpx;background:#efe1df}.wechat{display:flex;align-items:center;justify-content:center;height:82rpx;margin:0;border:2rpx solid #ecdedd;border-radius:22rpx;background:#fff;color:#6f5757;font-size:26rpx}.wechat:after{border:0}.wechat-icon{margin-right:13rpx;color:#37b56b;font-size:32rpx}.footer{position:relative;z-index:2;display:flex;align-items:center;justify-content:center;gap:9rpx;margin-top:28rpx;color:#bea4a2;font-size:20rpx}.footer-heart{color:#e67b86;animation:pulse 1.8s infinite}.modal-mask{position:fixed;z-index:20;inset:0;display:flex;align-items:center;justify-content:center;padding:40rpx;background:rgba(61,39,42,.45);backdrop-filter:blur(8rpx)}.wechat-modal{position:relative;box-sizing:border-box;width:600rpx;padding:42rpx;border-radius:36rpx;background:#fffaf7;text-align:center;box-shadow:0 30rpx 80rpx rgba(52,28,31,.25)}.modal-close{position:absolute;right:28rpx;top:20rpx;color:#b69c9a;font-size:48rpx}.mini-brand{color:#d86374;font-size:25rpx;font-weight:700}.modal-title{display:block;margin:20rpx 0 26rpx;color:#5b4244;font-size:36rpx;font-weight:700}.qr-shell{position:relative;display:flex;align-items:center;justify-content:center;width:270rpx;height:270rpx;margin:0 auto 22rpx;border:16rpx solid #fff;border-radius:18rpx;background:repeating-linear-gradient(45deg,#46383a 0 8rpx,#fff 8rpx 15rpx);box-shadow:0 8rpx 30rpx rgba(73,48,52,.13)}.qr-pattern{display:grid;grid-template-columns:1fr 1fr;gap:42rpx;color:#fff;font-size:50rpx;text-shadow:0 0 3rpx #46383a}.qr-logo{position:absolute;display:flex;align-items:center;justify-content:center;width:58rpx;height:58rpx;border:8rpx solid #fff;border-radius:18rpx;background:#e36f7e;color:#fff}.modal-tip{display:block;color:#5d4547;font-size:25rpx}.modal-note{display:block;margin-top:13rpx;color:#b29a98;font-size:19rpx;line-height:30rpx}@keyframes float{0%,100%{transform:translateY(0) rotate(-7deg);opacity:.25}50%{transform:translateY(-22rpx) rotate(8deg);opacity:.65}}@keyframes pulse{0%,100%{transform:scale(.88);opacity:.55}50%{transform:scale(1.18);opacity:1}}@keyframes breathe{0%,100%{margin-bottom:0}50%{margin-bottom:5rpx}}@media (min-width:760px){.page{max-width:820rpx;margin:0 auto;padding-top:42rpx}.illustration{height:220rpx}.card{padding-left:42rpx;padding-right:42rpx}}
</style>
