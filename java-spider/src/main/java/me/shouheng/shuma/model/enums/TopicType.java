package me.shouheng.shuma.model.enums;

/**
 * 话题类型枚举，主要对话题类型进行归类，前端可以根据话题的类型做不同的 ui 展示，
 * 比如特殊时节的运营活动可以通过设置不同的话题类型来实现。
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2020/1/26 11:07
 */
public enum TopicType {
    // 普通类型的话题
    NORMAL(0),
    // 欢迎类型的话题
    WELCOME(1);

    public final int id;

    TopicType(int id) {
        this.id = id;
    }

    public static TopicType getTypeById(int id) {
        for (TopicType type : values()) {
            if (type.id == id) {
                return type;
            }
        }
        return null;
    }
}
