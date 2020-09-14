package me.shouheng.shuma.anno;

import java.lang.annotation.*;

/**
 * 自定义注解，表的备注
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019/9/22 11:03
 */
@Documented
@Retention(RetentionPolicy.RUNTIME)
@Target(value = {ElementType.TYPE})
public @interface TableDefinition {

    /**
     * 备注的内容
     *
     * @return 备注的内容
     */
    String comment() default "";

    /**
     * 是否生成该类的 schema 类，schema 类是一个枚举类，其中的枚举值是 po 对象的各个字段的枚举值。
     *
     * 1. 如果返回结果为 true，会为该 po 所有字段生成 schema，
     *    而不论该 po下面的字段设置 {@link ColumnDefinition#genSchema()} 的值。
     * 2. 如果返回结果为 false，而 po 中的某个字段设置了 {@link ColumnDefinition#genSchema()} 为 true
     *    会为该对象的指定的字段生成 schema。
     *
     * @return true 表示生成 schema 枚举值
     */
    boolean genSchema() default false;
}
