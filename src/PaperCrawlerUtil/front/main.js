function export_xls(range){
        obj = {
            "range": range,
            "c": db_info
        };
        $.ajax({
            type:"post",
            url:export_link,
            data:JSON.stringify(obj),
            dataType:'json',
            success:function(result){
                alert("导出成功");
            },
            error:function(result){
                alert(result);
            }
        });
    }

function delete_ids(range){
    obj = {
        "range": range,
        "c": db_info
    };
    $.ajax({
        type:"post",
        url:delete_link,
        data:JSON.stringify(obj),
        dataType:'json',
        success:function(result){
            if(result["data"] === "True"){
                alert("删除成功");
                reqnext(initno=undefined, neg=0, refresh=1);
            }
            else{
                alert("删除失败，注意范围是左闭右开的集合，即输入(1,2),会报错，应该输入(1,3),如果删除单个值，需要使用(1)");
            }
        },
        error:function(result){
            alert(result);
        }
    });
}

function getElementByClassName(classnames){
    var objArray= new Array([]);//定义返回对象数组
    var tags=document.getElementsByTagName("*");//获取页面所有元素
    var index = 0;
    for(var i in tags){
        if(tags[i].nodeType===1){
            if(tags[i].getAttribute("class") === classnames){ //如果某元素的class值为所需要
                objArray[index]=tags[i];
                index++;
            }
        }
    }
    return objArray;
}



function pageChange(initno, neg, refresh, pageno){
    if (typeof(initno) === "undefined"){
        pageno = getElementByClassName("info")[0].firstElementChild.firstElementChild.children[1].innerHTML;
        pageno = parseInt(pageno, 10);
        if(neg === 1){
            pageno = pageno - 1;
        }
        else if(refresh === 1){
            pageno = pageno;
        }
        else{
            pageno = pageno + 1;
        }
    }
    else{
        pageno = pageno;
    }
    pages = getElementByClassName("pageno");
    for(i=0; i<pages.length; ++i){
        pages[i].value = pages[0].value;
    }
    obj = {
        "c": db_info,
        "page":parseInt(pages[0].value),
        "no":pageno
    };
    $.ajax({
        type:"post",
        url:change_page_link,
        data:JSON.stringify(obj),
        dataType:'json',
        success:function(result){
            pre = "<thead><tr><th>operation</th><th>id</th><th>file_execute</th><th>execute_time</th><th>finish_time</th><th>result</th>" +
            "<!--<th>parameter</th>-->" +
            "<th>comment</th>" +
            "<!--<th>default1</th><th>default2</th><th>default3</th><th>default4</th>--><!--<th>delete_flag</th>--></tr></thead>";
            var table = document.getElementById("main");
            sum_tr = "";
            for(var i =0; i < result["data"]["data"].length; i++){
                tr = "<tr>";
                tr = tr + "<td>" +
                                "<a href=\"javascript:void(0);\" onclick=\"deleteTr(this)\" >删除</a> " +
                                "<a href=\"javascript:void(0);\" onclick=\"modifyTr(this)\" >修改</a> " +
                                "<a href=\"javascript:void(0);\" onclick=\"detail(this)\" >详情</a> " +
                            "</td>";
                for(var j = 0; j < result['data']['data'][i].length; ++j){
                    if(j === 11 || j === 5 || j=== 10 || j === 9 || j === 8 || j=== 7){
                        //tr = tr + "<td>" + "前端不显示，请导出查看" + "</td>";
                    }
                    else{
                        tr = tr + "<td>" + result["data"]["data"][i][j] + "</td>";
                    }
                }
                tr = tr + "</tr>";
                tr = tr + "\n";
                sum_tr = sum_tr + tr;
            }
            table.innerHTML = pre + sum_tr;
            tds = getElementByClassName("sum");
            for(i=0; i<tds.length; ++i){
                tds[i].innerHTML = "共" + (parseInt(result["data"]["sum"]) - 1) + "页";
            }
            for(var i = 0; i < getElementByClassName("info").length; ++i){
                getElementByClassName("info")[i].firstElementChild.firstElementChild.children[1].innerHTML = pageno
            }
            pages = getElementByClassName("page");
            if(pages[0].innerHTML == 0){
                lefts = getElementByClassName("left");
                for(i = 0; i < lefts.length; ++i){
                    lefts[i].disabled = true;
                }
            }
            else{
                lefts = getElementByClassName("left");
                for(i = 0; i < lefts.length; ++i){
                    lefts[i].disabled = false;
                }
            }
            tds = getElementByClassName("sum");
            if("共" + pages[0].innerHTML + "页" === tds[0].innerHTML){
                rights = getElementByClassName("right");
                for(i = 0; i < rights.length; ++i){
                    rights[i].disabled = true;
                }
            }
            else{
                rights = getElementByClassName("right");
                for(i = 0; i < rights.length; ++i){
                    rights[i].disabled = false;
                }
            }
        },
        error:function(result){
            alert(result);
        }
    });

}


function get_id(id){
    obj = {
        "id": id,
        "c": db_info
    };
    $.ajax({
        type:"post",
        url:get_id_link,
        data:JSON.stringify(obj),
        dataType:'json',
        success:function(result){
            alert(result["data"]);
        },
        error:function(result){
            alert(result);
        }
    });
}


function reqnext(initno, neg, refresh){
    if (initno == 0){
        obj = {
        "c": db_info,
        "page":100,
        "no": 0
        };
        var sums = 0;
        $.ajax({
            type:"post",
            url:change_page_link,
            data:JSON.stringify(obj),
            dataType:'json',
            success:function(result){
                sums = parseInt(result["data"]["sum"]);
                pageChange(initno, neg, refresh, sums - 1);
            },
            error:function(result){
                alert(result);
            }
        });
    }

    pageChange(initno, neg, refresh, 0);

}
function detail(object) {
    var id = object.parentNode.parentNode.children[1].innerHTML;
    get_id(id);
}

function modifyTr(object) {
    var id = object.parentNode.parentNode.children[1].innerHTML;
    var comment = prompt("please input comment：", "xxx");
    if(comment.length === 0){
        return;
    }
    var data = {
        "id": id,
        "other": comment,
        "c": db_info
    };
    $.ajax(
        {
            type:"post",
            url: modify_link,
            data:JSON.stringify(data),
            dataType:'json',
            success:function(result){
                if(result["data"] === "True"){
                    alert("success");
                    reqnext(initno=undefined, neg=0, refresh=1)
                }
                else{
                    alert("failure");
                }
            }, error: function(result){
                alert(result);
            }
        });
}
