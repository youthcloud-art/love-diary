<script setup lang="ts">
import {ref} from "vue";import {request} from "../../api";import {onShow} from "@dcloudio/uni-app";
const name=ref("我们的日记"),code=ref("");async function check(){try{await request("/api/v1/spaces/current");uni.switchTab({url:"/pages/index/index"})}catch{}}
async function create(){try{await request("/api/v1/spaces","POST",{name:name.value});uni.switchTab({url:"/pages/index/index"})}catch(e){tip(e)}}async function join(){try{await request("/api/v1/spaces/join","POST",{code:code.value});uni.switchTab({url:"/pages/index/index"})}catch(e){tip(e)}}function tip(e:any){uni.showToast({title:e.message,icon:"none"})}onShow(check);
</script>
<template><view class="page"><text class="lead">创建一本日记，或者输入另一半的邀请码。</text><view class="card"><input v-model="name"/><button @click="create">创建双人空间</button></view><view class="card"><input v-model="code" placeholder="6 位邀请码"/><button class="outline" @click="join">加入空间</button></view></view></template>
<style scoped>.page{padding:48rpx}.lead{display:block;color:#8a6a6a;margin-bottom:30rpx}.card{background:white;padding:30rpx;border-radius:24rpx;margin-bottom:24rpx}input{background:#fff7f3;padding:22rpx;border-radius:16rpx}button{background:#c45c6a;color:white;margin-top:20rpx}.outline{background:white;color:#c45c6a;border:2rpx solid #ecc2c8}</style>

