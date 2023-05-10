
var show_;
function change_()
{
let get_storing = document.getElementById('mission_storing');
let get_moving = document.getElementById('mission_moving');
let get_retrieving = document.getElementById('mission_retrieving');
let get_buc = document.getElementById('mission_buc');
let get_mission_storing = document.getElementById('storing');
let get_mission_moving = document.getElementById('moving');
let get_mission_retrieving = document.getElementById('retrieving');
let get_mission_buc = document.getElementById('buc_sto_or_ret');
if (get_storing.checked)
{
get_mission_retrieving.setAttribute('hidden',true)
get_mission_moving.setAttribute('hidden',true)
get_mission_buc.setAttribute('hidden',true)
get_mission_storing.removeAttribute('hidden')
}
else if (get_moving.checked)
{
get_mission_retrieving.setAttribute('hidden',true)
get_mission_storing.setAttribute('hidden',true)
get_mission_buc.setAttribute('hidden',true)
get_mission_moving.removeAttribute('hidden')
}
else if (get_retrieving.checked)
{
get_mission_storing.setAttribute('hidden',true)
get_mission_moving.setAttribute('hidden',true)
get_mission_buc.setAttribute('hidden',true)
get_mission_retrieving.removeAttribute('hidden')
}
else if (get_buc.checked)
{
get_mission_storing.setAttribute('hidden',true)
get_mission_moving.setAttribute('hidden',true)
get_mission_retrieving.setAttribute('hidden',true)
get_mission_buc.removeAttribute('hidden')
}
}

function con_(){
var ip = document.getElementById('inputGroup-IP');
var port = document.getElementById('inputGroup-PORT');
var username = document.getElementById('inputGroup-USERNAME');
var password = document.getElementById('inputGroup-PASSWORD');
var cu = document.getElementById('inputGroup-ROUTING_KEY');
$.ajax({
url:'/dispatch_con',
type:'GET',
data:{
ip:ip.value,
port:port.value,
username:username.value,
password:password.value,
cu:cu.value
},
success:function(data){
alert(data)
}
})
}

function start_storing()
{
let rack_id = document.getElementById('stor_id').value
let rack = document.getElementById('stor_rack').value
let tube = document.getElementById('stor_tube').value
if (document.getElementById('is_use_weigh').checked){
var buc_min = Number(document.getElementById('stor_min').value)
var buc_max = Number(document.getElementById('stor_max').value)
}
else{
var buc_min = -1
var buc_max = -1
}

let is_source = document.getElementById('is_source_rack')
let is_return_buc = document.getElementById('is_back_bucket')
if(is_source.checked)
{var is_source_value = 1}
else
{var is_source_value = 0}
if(is_return_buc.checked)
{var is_return_buc_val = 1}
else
{var is_return_buc_val = 0}
var but_sto = document.getElementById("but_storing");
var staticBackdrop = document.getElementById("staticBackdrop")
if(rack_id==''||rack == ''||tube == '' ||buc_max == ''||buc_min ==''){
alert('请填写完整数据信息')}
else{

var data = JSON.stringify({"rack_id":rack_id,"rack":rack,"tube":tube,"buc_min":buc_min,"buc_max":buc_max,"is_source":is_source_value,"is_return_buc":is_return_buc_val
})
show_=setInterval(show_status,2000);
$(staticBackdrop).modal('show')
$.ajax({
url:'/dispatch_storing',
type:'POST',
data:data,
success:function(msg){
alert(msg)
}
})
}
}


function start_moving()
{
let source_rack = document.getElementById('input-moving_source').value
let target_rack = document.getElementById('input-moving_target').value
let rack = document.getElementById('input-moving-rack').value
let tube = document.getElementById('input-moving-tube').value
let source_not_move = document.getElementById('source_not_move').value
let target_not_move = document.getElementById('target_not_move').value
let source_move = document.getElementById('source_move').value
let target_move = document.getElementById('target_move').value
let tube_num = document.getElementById('tube_num').value
var staticBackdrop = document.getElementById("staticBackdrop")
if (source_rack==''||target_rack==''||rack==''||tube==''||source_not_move==''||target_not_move==''||source_move==''
||target_move==''||tube_num==''){
alert('请填写完整信息')
}
else{
data = JSON.stringify({"source_rack":source_rack,"target_rack":target_rack,"rack":rack,"tube":tube,
"source_not_move":source_not_move,"target_not_move":target_not_move,"source_move":source_move,
"target_move":target_move,"tube_num":tube_num
});
$(staticBackdrop).modal('show');
show_ = setInterval(show_status,2000);
$.ajax({
url:'/dispatch_moving',
type:'POST',
data:data,
success:function(msg){
alert(msg)
}
})
}
}


function start_retrieving()
{
let rack_id = document.getElementById('input-retrieving').value
let rack = document.getElementById('input-retrieving-rack').value
let tube = document.getElementById('input-retrieving-tube').value
if (document.getElementById('is_use_weigh_ret').checked){
var buc_min = Number(document.getElementById('retrieving-weigh_min').value)
var buc_max = Number(document.getElementById('retrieving-weigh_target').value)
}
else{
var buc_min = -1
var buc_max = -1
}

let is_receive_bucket = document.getElementById('is_receive_bucket')
if(is_receive_bucket.checked)
{var is_receive_bucket_value = 1}
else
{var is_receive_bucket_value = 0}
var staticBackdrop = document.getElementById("staticBackdrop")
if (rack_id==''||rack ==''||tube==''||buc_min==''||buc_max==''){
alert('请填写完整信息')}
else{
var data = JSON.stringify({"rack_id":rack_id,"rack":rack,"tube":tube,"buc_min":buc_min,
"buc_max":buc_max,"is_receive_bucket":is_receive_bucket_value
})
$(staticBackdrop).modal('show')
show_ = setInterval(show_status,2000);
$.ajax({
url:'/dispatch_retrieving',
type:'POST',
data:data,
success:function(msg){
alert(msg)
}
})
}}


function start_buc_storing()
{
$(staticBackdrop).modal('show')
show_ = setInterval(show_status,2000);
$.ajax({
url:'/dispatch_buc_sto',
type:'POST',
success:function(msg){
alert(msg)
}
})
}

function start_buc_retrieving()
{
$(staticBackdrop).modal('show')
show_ = setInterval(show_status,2000);
$.ajax({
url:'/dispatch_buc_ret',
type:'POST',
success:function(msg){
alert(msg)
}
})
}


function show_status(){
$.ajax({
url:'/show_status',
type:'GET',
async: false,
success:function(data){
var show_content = document.getElementById('show_status');
if (data != 'None'){
var reg = RegExp('开始')
var mes_close = RegExp('waiting_close')
if (data.match(reg)){
show_content.innerHTML = data +'<br>'
}
else if (data == 'end'){
clearInterval(show_)
}
else{
show_content.innerHTML += data +'<br>'
if (data.match(mes_close)){
alert('请放入或取出转运桶后，选择确定按钮关门')
$.ajax({
url:'/close_door',
type:'GET',
async:false
})
}
}
}}
})
}


function if_weigh_stor(){
  var is_use_weigh = document.getElementById('is_use_weigh');
  var weigh_min = document.getElementById('stor_min');
  var weigh_max = document.getElementById('stor_max');
  if (is_use_weigh.checked)
  {
    weigh_min.removeAttribute('disabled');
    weigh_max.removeAttribute('disabled')
  }
  else{
    weigh_min.setAttribute('disabled',true);
    weigh_max.setAttribute('disabled',true)
  }
  }

function if_weigh_retr(){
  var is_use_weigh = document.getElementById('is_use_weigh_ret');
  var weigh_min = document.getElementById('retrieving-weigh_min');
  var weigh_max = document.getElementById('retrieving-weigh_target');
  if (is_use_weigh.checked)
  {
    weigh_min.removeAttribute('disabled');
    weigh_max.removeAttribute('disabled')
  }
  else{
    weigh_min.setAttribute('disabled',true);
    weigh_max.setAttribute('disabled',true)
  }
  }