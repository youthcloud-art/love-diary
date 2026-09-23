<script setup lang="ts">
import {ref} from "vue";import {auth,token} from "../../api";import {onShow} from "@dcloudio/uni-app";
const register=ref(false),nickname=ref("恋人"),email=ref("a@example.com"),password=ref("secret123");
async function go(){try{await auth(register.value?"register":"login",{nickname:nickname.value,email:email.value,password:password.value});uni.redirectTo({url:"/pages/space/space"})}catch(e){uni.showToast({title:(e as Error).message,icon:"none"})}}
function wx(){uni.login({success:async r=>{await auth("wechat",{code:r.code});uni.redirectTo({url:"/pages/space/space"})}})}
onShow(()=>{if(token())uni.redirectTo({url:"/pages/space/space"})});
</script>
<template><view class="page"><text class="logo">恋爱日记</text><text class="sub">两人一本，收藏共同的时光</text><view class="card"><input v-if="register" v-model="nickname" placeholder="昵称"/><input v-model="email" placeholder="邮箱"/><input v-model="password" password placeholder="密码"/><button @click="go">{{register?'注册并开始':'登录'}}</button><text class="switch" @click="register=!register">{{register?'已有账号？登录':'没有账号？注册'}}</text><button class="wx" @click="wx">微信一键登录</button></view></view></template>
<style scoped>.page{padding:120rpx 44rpx}.logo{display:block;font-size:64rpx;font-weight:700;color:#c45c6a}.sub{display:block;margin:16rpx 0 60rpx;color:#9b7379}.card{background:white;padding:36rpx;border-radius:28rpx}input{background:#fff7f3;padding:22rpx;margin-bottom:18rpx;border-radius:16rpx}button{background:#c45c6a;color:white;margin-top:20rpx}.switch{display:block;text-align:center;color:#c45c6a;margin:26rpx}.wx{background:#36a65c}</style>

