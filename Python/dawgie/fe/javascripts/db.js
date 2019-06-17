// COPYRIGHT:
function db_compare(t,e){return t.id<e.id?-1:t.id>e.id?1:0}function db_compare_num(t,e){return Number(t)<Number(e)?-1:Number(t)>Number(e)?1:0}function db_item_ref(t){return'<a href="/app/db/item?path='+t.path+'">'+t.id+"</a>"}function db_load(){db_targets(),db_versions(),db_prime()}function db_lockview(){function t(t){var e=document.getElementById("lockview"),n="";for(t.msg&&(n+=t.msg),k=0;k<t.tasks.length;k++)n+="<li>"+t.tasks[k]+"</li>";e.innerHTML=n}var e=new XMLHttpRequest;e.onreadystatechange=function(){4==e.readyState&&200==e.status&&t(JSON.parse(e.responseText))},"undefined"==typeof local_app_db_lockview?(e.open("GET","/app/db/lockview"),e.send()):t(JSON.parse(local_app_db_lockview))}function db_prime(){var t=new XMLHttpRequest;t.onreadystatechange=function(){4==t.readyState&&200==t.status&&(db_prime_table=JSON.parse(t.responseText),db_prime_org())},"undefined"==typeof local_app_db_prime?(t.open("GET","/app/db/prime"),t.send()):(db_prime_table=JSON.parse(local_app_db_prime),db_prime_org())}function db_prime_0(t){var e,n=[],s="<tbody><tr><th>State Vector</th><th>Target Name</th><th>Run ID</th></tr>";for(i=0;i<db_prime_table.length;i++)svn=db_prime_table[i].split("."),n.push(svn.slice(2,svn.length).join("."));for(n=db_unique(n),n.sort(),i=0;i<n.length;i++){var o=[];for(p=0;p<db_prime_table.length;p++)if(e=db_prime_table[p].split("."),e.slice(2,e.length).join(".")===n[i]){var a=-1,l=Number(e[0]),u=e[1];for(c=0;c<o.length;c++)o[c].id===u&&(a=c);0>a&&(o.push({id:u,rids:[]}),a=o.length-1),o[a].rids.push({id:l,path:db_prime_table[p]})}for(o.sort(db_compare),c=0;c<o.length;c++){var h="";for(o[c].rids.sort(db_compare),r=0;r<o[c].rids.length-1;r++)h+=db_item_ref(o[c].rids[r])+", ";h+=db_item_ref(o[c].rids[o[c].rids.length-1]),s+=0===c?'<tr><td rowspan="'+o.length+'">'+n[i]+"</td><td>"+o[c].id+"</td><td>"+h+"</td></tr>":"<tr><td>"+o[c].id+"</td><td>"+h+"</td></tr>"}}s+="</tbody>",t.innerHTML=s}function db_prime_1(t){var e,n=[],o="<tbody><tr><th>Run ID</th><th>Target Name</th><th>State Vector</th></tr>";for(i=0;i<db_prime_table.length;i++)n.push(db_prime_table[i].split(".")[0]);for(n=db_unique(n),n.sort(db_compare_num),r=0;r<n.length;r++){var a=[],l=0;for(p=0;p<db_prime_table.length;p++)if(e=db_prime_table[p].split("."),e[0]===n[r]){var u=-1,h=(n[r],e.slice(2,e.length).join(".")),d=e[1];for(c=0;c<a.length;c++)a[c].id===d&&(u=c);0>u&&(a.push({id:d,svns:[]}),u=a.length-1),a[u].svns.push({id:h,path:db_prime_table[p]})}for(a.sort(db_compare),c=0;c<a.length;c++)l+=a[c].svns.length;for(c=0;c<a.length;c++)for(a[c].svns.sort(db_compare),s=0;s<a[c].svns.length;s++)o+=0===c&&0===s?'<tr><td rowspan="'+l+'">'+n[r]+'</td><td rowspan="'+a[c].svns.length+'">'+a[c].id+"</td><td>"+db_item_ref(a[c].svns[s])+"</td></tr>":0===s?'<tr><td rowspan="'+a[c].svns.length+'">'+a[c].id+"</td><td>"+db_item_ref(a[c].svns[s])+"</td></tr>":"<tr><td>"+db_item_ref(a[c].svns[s])+"</td></tr>"}o+="</tbody>",t.innerHTML=o}function db_prime_2(e){var n,s=[],o="<tbody><tr><th>Target Name</th><th>State Vector</th><th>Run ID</th></tr>";for(i=0;i<db_prime_table.length;i++)s.push(db_prime_table[i].split(".")[1]);for(s=db_unique(s),s.sort(),t=0;t<s.length;t++){var a=[];for(p=0;p<db_prime_table.length;p++)if(n=db_prime_table[p].split("."),n[1]===s[t]){var l=-1,u=Number(n[0]),h=n.slice(2,n.length).join(".");s[t];for(c=0;c<a.length;c++)a[c].id===h&&(l=c);0>l&&(a.push({id:h,rids:[]}),l=a.length-1),a[l].rids.push({id:u,path:db_prime_table[p]})}for(a.sort(db_compare),c=0;c<a.length;c++){var d="";for(a[c].rids.sort(db_compare),r=0;r<a[c].rids.length-1;r++)d+=db_item_ref(a[c].rids[r])+", ";d+=db_item_ref(a[c].rids[a[c].rids.length-1]),o+=0===c?'<tr><td rowspan="'+a.length+'">'+s[t]+"</td><td>"+a[c].id+"</td><td>"+d+"</td></tr>":"<tr><td>"+a[c].id+"</td><td>"+d+"</td></tr>"}}o+="</tbody>",e.innerHTML=o}function db_prime_org(){var t=document.getElementById("org"),e=document.getElementById("prime");switch(Number(t.value)){case 0:db_prime_0(e);break;case 1:db_prime_1(e);break;case 2:db_prime_2(e);break;default:console.log("Should not be here and it means there are new options that I am not programmed to handle!!"),e.innerHTML="<p>Should not be here and it means there are new options that I am not programmed to handle!!</p>"}}function db_targets(){function t(t){var e=document.getElementById("targets");if(0===t.length)e.innerHTML="<p>No known targets</p>";else for(t.sort(),i=0;i<t.length;i++)e.innerHTML+="<li class=list-group-item>"+t[i]+"</li>"}var e=new XMLHttpRequest;e.onreadystatechange=function(){4==e.readyState&&200==e.status&&t(JSON.parse(e.responseText))},"undefined"==typeof local_app_db_targets?(e.open("GET","/app/db/targets"),e.send()):t(JSON.parse(local_app_db_targets))}function db_unique(t){var e=[],n={};for(i=0;i<t.length;i++)n.hasOwnProperty(t[i])||(e.push(t[i]),n[t[i]]=!0);return e}function db_ver(t){var e="";if(0<t.length){for(i=0;i<t.length-1;i++)e+=t[i]+", ";e+=t[t.length-1]}return e}function db_versions(){function t(t){var e=document.getElementById("algs"),n=document.getElementById("statevectors"),r=document.getElementById("tasks"),i=document.getElementById("values");if(0===t.length)e.innerHTML="<p>No known versions</p>",n.innerHTML="<p>No known versions</p>",r.innerHTML="<p>No known tasks</p>",i.innerHTML="<p>No known versions</p>";else{var s=Object.keys(t[0]);for(s.sort(),k=0;k<s.length;k++)r.innerHTML+="<li class=list-group-item>"+s[k]+"</li>";for(s=Object.keys(t[1]),s.sort(),k=0;k<s.length;k++)e.innerHTML+="<li class=list-group-item>"+s[k]+" : ["+db_ver(t[1][s[k]])+"]</li>";for(s=Object.keys(t[2]),s.sort(),k=0;k<s.length;k++)n.innerHTML+="<li class=list-group-item>"+s[k]+" : ["+db_ver(t[2][s[k]])+"]</li>";for(s=Object.keys(t[3]),s.sort(),k=0;k<s.length;k++)i.innerHTML+="<li class=list-group-item>"+s[k]+" : ["+db_ver(t[3][s[k]])+"]</li>"}}var e=new XMLHttpRequest;e.onreadystatechange=function(){4==e.readyState&&200==e.status&&t(JSON.parse(e.responseText))},"undefined"==typeof local_app_db_versions?(e.open("GET","/app/db/versions"),e.send()):t(JSON.parse(local_app_db_versions))}var db_prime_table;